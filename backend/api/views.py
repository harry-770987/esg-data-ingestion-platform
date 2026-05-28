from datetime import date, datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import Tenant, DataSource, UploadBatch, EmissionRecord, AuditLog, ApprovalHistory
from api.serializers import (
    UploadBatchSerializer, EmissionRecordSerializer, 
    AuditLogSerializer, ApprovalHistorySerializer
)
from api.permissions import HasTenantPermission, IsRecordUnlocked
from api.pagination import StandardResultsSetPagination
from api.filters import EmissionRecordFilter
from ingestion.pipeline import IngestionPipeline
from ingestion.normalizers import ValueNormalizer
from ingestion.validators import RowValidator
from ingestion.constants import SOURCE_TYPE_METADATA

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_status(request):
    """
    Status / Health Check endpoint.
    """
    return Response({
        "status": "online",
        "platform": "ESG Ingestion Platform API",
        "version": "1.0.0"
    })


class UploadBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving CSV ingestion batches.
    Includes custom action /upload/ to process CSV uploads.
    """
    serializer_class = UploadBatchSerializer
    permission_classes = [HasTenantPermission]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Filter all batches by request tenant (from header permission)
        return UploadBatch.objects.filter(tenant=self.request.tenant).order_by('-created_at')

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Receives a CSV file and a source type, creates an UploadBatch, 
        and runs the ingestion pipeline.
        """
        source_type = request.data.get('source_type')
        if not source_type:
            return Response({"error": "source_type parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if source_type not in SOURCE_TYPE_METADATA:
            return Response(
                {"error": f"Invalid source_type. Supported values: {list(SOURCE_TYPE_METADATA.keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file was supplied in the request."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve or dynamically create a standard default DataSource for this Tenant
        data_source = DataSource.objects.filter(tenant=request.tenant, source_type=source_type).first()
        if not data_source:
            data_source = DataSource.objects.create(
                tenant=request.tenant,
                name=f"Standard {source_type} Source",
                source_type=source_type,
                description="Auto-created standard ingestion source"
            )

        try:
            batch = IngestionPipeline.ingest(
                tenant_id=request.tenant.id,
                data_source_id=data_source.id,
                file_name=file_obj.name,
                file_source=file_obj,
                uploaded_by=request.user if request.user.is_authenticated else None
            )
        except Exception as e:
            # Retrieve the failed batch to inspect processing errors
            failed_batch = UploadBatch.objects.filter(
                tenant=request.tenant, 
                file_name=file_obj.name
            ).order_by('-created_at').first()
            
            if failed_batch:
                serializer = self.get_serializer(failed_batch)
                return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmissionRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing EmissionRecords.
    Supports standard listings, details, edits, and custom approval flows.
    """
    serializer_class = EmissionRecordSerializer
    permission_classes = [HasTenantPermission, IsRecordUnlocked]
    pagination_class = StandardResultsSetPagination
    filterset_class = EmissionRecordFilter

    def get_queryset(self):
        # Prevent N+1 queries by pre-fetching related objects
        return EmissionRecord.objects.filter(
            tenant=self.request.tenant
        ).select_related('data_source', 'upload_batch').order_by('-transaction_date')

    @action(detail=False, methods=['get'], url_path='suspicious')
    def suspicious(self, request):
        """
        Retrieves all records containing structural or numerical validation warnings.
        """
        queryset = self.get_queryset().filter(suspicious=True)
        
        # Re-apply filters on the queryset slice
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        # 1. Obtain instance states before saving
        instance = self.get_object()
        tracked_fields = ['quantity', 'unit', 'activity_type', 'transaction_date']
        previous_values = {field: getattr(instance, field) for field in tracked_fields}
        
        # Serialize fields for clean JSON logs
        from decimal import Decimal
        for k, v in previous_values.items():
            if isinstance(v, (date, datetime)):
                previous_values[k] = v.isoformat()
            elif isinstance(v, Decimal):
                previous_values[k] = float(v)

        # 2. Save the primary serializer changes
        updated_instance = serializer.save()

        # Check if raw values changed
        raw_changed = False
        for field in tracked_fields:
            if getattr(updated_instance, field) != getattr(instance, field):
                raw_changed = True
                break

        # 3. If values changed, recompute calculations and validate
        if raw_changed:
            source_type = updated_instance.data_source.source_type
            meta = SOURCE_TYPE_METADATA.get(source_type)
            
            if meta:
                # Recalculate normalized values
                norm_qty, norm_unit = ValueNormalizer.normalize_unit(
                    updated_instance.quantity, 
                    updated_instance.unit, 
                    meta['standard_unit']
                )
                updated_instance.normalized_quantity = norm_qty
                updated_instance.normalized_unit = norm_unit
                updated_instance.scope = meta['scope']
                updated_instance.category = meta['category']

            # Parse date format safely
            updated_instance.transaction_date = ValueNormalizer.normalize_date(updated_instance.transaction_date)

            # Recheck validation anomalies
            row_dict = {
                'quantity': updated_instance.quantity,
                'unit': updated_instance.unit,
                'normalized_quantity': updated_instance.normalized_quantity,
                'normalized_unit': updated_instance.normalized_unit,
                'transaction_date': updated_instance.transaction_date,
            }
            validated_row = RowValidator.validate_batch([row_dict])[0]
            updated_instance.suspicious = validated_row.get('suspicious', False)
            updated_instance.suspicious_reasons = validated_row.get('suspicious_reasons', [])
            updated_instance.save()

            # 4. Save AuditLog entry
            new_values = {field: getattr(updated_instance, field) for field in tracked_fields}
            for k, v in new_values.items():
                if isinstance(v, (date, datetime)):
                    new_values[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    new_values[k] = float(v)

            AuditLog.objects.create(
                emission_record=updated_instance,
                changed_by=self.request.user if self.request.user.is_authenticated else None,
                action='EDIT',
                previous_values=previous_values,
                new_values=new_values
            )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approves an emission record and locks it to prevent future modifications.
        """
        record = self.get_object()
        
        # Secondary lock check (handled by permission class, but good defense in depth)
        if record.locked:
            raise PermissionDenied("Record is locked and cannot be approved.")

        comments = request.data.get('comments', '')

        with transaction.atomic():
            # Log approval step
            ApprovalHistory.objects.create(
                emission_record=record,
                reviewed_by=request.user if request.user.is_authenticated else None,
                action='APPROVE',
                comments=comments
            )
            # Log lock change in audit ledger
            AuditLog.objects.create(
                emission_record=record,
                changed_by=request.user if request.user.is_authenticated else None,
                action='LOCK'
            )
            # Mark record approved and lock it
            record.approved = True
            record.locked = True
            record.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Rejects an emission record (clears approved and locked states).
        """
        record = self.get_object()
        
        if record.locked:
            raise PermissionDenied("Record is locked and cannot be rejected.")

        comments = request.data.get('comments', '')

        with transaction.atomic():
            ApprovalHistory.objects.create(
                emission_record=record,
                reviewed_by=request.user if request.user.is_authenticated else None,
                action='REJECT',
                comments=comments
            )
            record.approved = False
            record.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock(self, request, pk=None):
        """
        Unlocks a previously approved/locked record to allow modifications.
        """
        record = self.get_object()
        
        if not record.locked:
            return Response({"detail": "Record is already unlocked."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Record unlock action in audit ledger
            AuditLog.objects.create(
                emission_record=record,
                changed_by=request.user if request.user.is_authenticated else None,
                action='UNLOCK'
            )
            record.locked = False
            record.approved = False
            record.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing historical AuditLogs. Read-Only ledger.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [HasTenantPermission]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Filter audit logs by verifying the tenant ID of the referenced records
        return AuditLog.objects.filter(
            emission_record__tenant=self.request.tenant
        ).select_related('emission_record', 'changed_by').order_by('-changed_at')
