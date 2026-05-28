import traceback
from datetime import date
import pandas as pd
from django.db import transaction
from core.models import Tenant, DataSource, UploadBatch, EmissionRecord
from .parsers import CSVParser
from .normalizers import ValueNormalizer
from .validators import RowValidator
from .exceptions import IngestionException, ParserError, ValidationError, NormalizationError

class IngestionPipeline:
    """
    Orchestrates the complete ESG CSV ingestion flow.
    Ensures transactional safety and records metadata in UploadBatch.
    """

    @classmethod
    def ingest(cls, tenant_id, data_source_id, file_name, file_source, uploaded_by=None) -> UploadBatch:
        # Resolve Tenant and DataSource first
        try:
            tenant = Tenant.objects.get(pk=tenant_id)
            data_source = DataSource.objects.get(pk=data_source_id, tenant=tenant)
        except (Tenant.DoesNotExist, DataSource.DoesNotExist) as e:
            raise ValidationError(f"Invalid Tenant or DataSource reference: {str(e)}")

        # 1. Create UploadBatch outside the transaction to preserve its record if ingestion fails.
        batch = UploadBatch.objects.create(
            tenant=tenant,
            data_source=data_source,
            uploaded_by=uploaded_by,
            file_name=file_name,
            status='PROCESSING'
        )

        try:
            # 2. Parse the CSV file into a standardized DataFrame
            df = CSVParser.parse(file_source, source_type=data_source.source_type)
            
            # 3. Use transaction.atomic to ensure database integrity of emission records
            with transaction.atomic():
                normalized_records = []
                
                # Iterate rows and normalize
                for index, row in df.iterrows():
                    # Strip out NaN values from raw data for clean JSON serialization
                    raw_row_data = {
                        str(k): (None if (hasattr(v, 'isna') and v.isna()) or (isinstance(v, float) and import_math_isnan(v)) else v)
                        for k, v in row.to_dict().items()
                    }
                    
                    # Normalize columns
                    norm_data = ValueNormalizer.normalize_record(raw_row_data, data_source.source_type)
                    
                    # Keep raw row data for audit traceability
                    norm_data['raw_data'] = raw_row_data
                    normalized_records.append(norm_data)

                # 4. Perform row validation and anomaly checks
                validated_records = RowValidator.validate_batch(normalized_records)

                # 5. Build and Bulk Insert EmissionRecord objects
                emission_records_to_create = []
                suspicious_count = 0
                
                for r in validated_records:
                    if r.get('suspicious', False):
                        suspicious_count += 1
                        
                    emission_records_to_create.append(
                        EmissionRecord(
                            tenant=tenant,
                            data_source=data_source,
                            upload_batch=batch,
                            category=r['category'],
                            activity_type=r['activity_type'],
                            transaction_date=r['transaction_date'] if r['transaction_date'] is not None and not pd.isna(r['transaction_date']) else date.today(),
                            quantity=r['quantity'] if r['quantity'] is not None else 0.0,
                            unit=r['unit'] or '',
                            normalized_quantity=r['normalized_quantity'],
                            normalized_unit=r['normalized_unit'],
                            scope=r['scope'],
                            suspicious=r.get('suspicious', False),
                            suspicious_reasons=r.get('suspicious_reasons', []),
                            raw_data=r['raw_data']
                        )
                    )
                
                # Bulk insert records for maximum performance
                EmissionRecord.objects.bulk_create(emission_records_to_create)

                # Update batch statistics
                total_rows = len(validated_records)
                batch.total_rows = total_rows
                batch.processed_rows = total_rows - suspicious_count
                batch.failed_rows = suspicious_count  # Treat suspicious rows as "warnings/failures" for dashboard counts
                batch.status = 'COMPLETED'
                batch.save()
                
        except Exception as e:
            # If any failure occurs, mark the batch as failed and log the stack trace
            batch.status = 'FAILED'
            batch.error_summary = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            batch.save()
            raise e

        return batch


def import_math_isnan(val):
    """Helper to check for float NaN values safely."""
    import math
    try:
        return math.isnan(val)
    except TypeError:
        return False
