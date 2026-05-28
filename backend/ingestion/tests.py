from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth.models import User
from core.models import Tenant, DataSource, UploadBatch, EmissionRecord
from ingestion.pipeline import IngestionPipeline
from ingestion.exceptions import ParserError, ValidationError
from ingestion.normalizers import ValueNormalizer
from ingestion.validators import RowValidator

class IngestionPipelineTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Acme Carbon Corp")
        self.user = User.objects.create_user(username="compliance_officer", password="password123")
        
        # Data Sources for the 3 categories
        self.sap_source = DataSource.objects.create(
            tenant=self.tenant,
            name="SAP Fuel Logs",
            source_type="SAP_FUEL"
        )
        self.utility_source = DataSource.objects.create(
            tenant=self.tenant,
            name="Electricity Grid Portal",
            source_type="UTILITY_ELEC"
        )
        self.travel_source = DataSource.objects.create(
            tenant=self.tenant,
            name="Expedia Travel Logs",
            source_type="TRAVEL_CORP"
        )

    def test_unit_conversion_normalization(self):
        """Verify standard unit conversions (gallons->L, MWh->kWh, miles->km) work."""
        # Gallons to Liters
        qty, unit = ValueNormalizer.normalize_unit(10.0, "gallons", "L")
        self.assertAlmostEqual(qty, 37.8541)
        self.assertEqual(unit, "L")
        
        # MWh to kWh
        qty, unit = ValueNormalizer.normalize_unit(2.5, "MWh", "kWh")
        self.assertEqual(qty, 2500.0)
        self.assertEqual(unit, "kWh")
        
        # Miles to km
        qty, unit = ValueNormalizer.normalize_unit(100.0, "miles", "km")
        self.assertAlmostEqual(qty, 160.934)
        self.assertEqual(unit, "km")

    def test_sap_fuel_csv_ingestion(self):
        """Verify successful ingestion and mapping of an SAP Fuel CSV."""
        csv_data = (
            "InvoiceNo,PostingDate,Vendor,FuelType,Quantity,Unit,Cost,PlantCode\n"
            "INV-001,2026-05-10,QuickGas,Diesel,10.0,gallons,45.0,PL-01\n"
            "INV-002,2026-05-11,QuickGas,Petrol,50.0,liters,90.0,PL-02\n"
        )
        
        batch = IngestionPipeline.ingest(
            tenant_id=self.tenant.id,
            data_source_id=self.sap_source.id,
            file_name="sap_fuel_q2.csv",
            file_source=csv_data,
            uploaded_by=self.user
        )
        
        self.assertEqual(batch.status, 'COMPLETED')
        self.assertEqual(batch.total_rows, 2)
        self.assertEqual(batch.processed_rows, 2)
        self.assertEqual(batch.failed_rows, 0)
        
        # Check database records
        records = EmissionRecord.objects.filter(upload_batch=batch)
        self.assertEqual(records.count(), 2)
        
        # Verify first row (10 gallons -> 37.8541 L)
        r1 = records.get(activity_type="Diesel")
        self.assertEqual(r1.category, "SCOPE_1_FUEL")
        self.assertEqual(r1.scope, 1)
        self.assertAlmostEqual(float(r1.normalized_quantity), 37.8541)
        self.assertEqual(r1.normalized_unit, "L")
        self.assertEqual(r1.transaction_date, date(2026, 5, 10))
        self.assertEqual(r1.raw_data["invoiceno"], "INV-001")
        
        # Verify second row (50 liters -> 50 L)
        r2 = records.get(activity_type="Petrol")
        self.assertEqual(r2.normalized_quantity, 50.0)
        self.assertEqual(r2.normalized_unit, "L")

    def test_utility_elec_csv_ingestion(self):
        """Verify successful ingestion of Utility Electricity CSV."""
        csv_data = (
            "BillingPeriodStart,BillingPeriodEnd,AccountNo,MeterID,UsageQuantity,UsageUnit,TotalCharge\n"
            "2026-04-01,2026-04-30,ELEC-123,M-101,1.5,MWh,225.00\n"
            "2026-05-01,2026-05-31,ELEC-123,M-101,200.0,kWh,30.00\n"
        )
        
        batch = IngestionPipeline.ingest(
            tenant_id=self.tenant.id,
            data_source_id=self.utility_source.id,
            file_name="utility_elec_q2.csv",
            file_source=csv_data,
            uploaded_by=self.user
        )
        
        self.assertEqual(batch.status, 'COMPLETED')
        self.assertEqual(batch.total_rows, 2)
        
        records = EmissionRecord.objects.filter(upload_batch=batch)
        r1 = records.get(quantity=1.5)
        self.assertEqual(r1.category, "SCOPE_2_ELEC")
        self.assertEqual(r1.scope, 2)
        self.assertEqual(r1.activity_type, "Electricity")
        self.assertEqual(r1.normalized_quantity, 1500.0)  # 1.5 MWh -> 1500 kWh
        self.assertEqual(r1.normalized_unit, "kWh")
        self.assertEqual(r1.transaction_date, date(2026, 4, 30))

    def test_travel_corp_csv_ingestion(self):
        """Verify successful ingestion of Travel Corporate CSV."""
        csv_data = (
            "BookingID,EmployeeID,TravelDate,Departure,Arrival,Distance,DistanceUnit,TransportType\n"
            "BK-01,EMP-01,2026-05-15,SFO,JFK,2500,miles,Flight\n"
            "BK-02,EMP-02,2026-05-16,LHR,CDG,350,km,Train\n"
        )
        
        batch = IngestionPipeline.ingest(
            tenant_id=self.tenant.id,
            data_source_id=self.travel_source.id,
            file_name="travel_q2.csv",
            file_source=csv_data,
            uploaded_by=self.user
        )
        
        self.assertEqual(batch.status, 'COMPLETED')
        self.assertEqual(batch.total_rows, 2)
        
        records = EmissionRecord.objects.filter(upload_batch=batch)
        r1 = records.get(activity_type="Flight")
        self.assertEqual(r1.category, "SCOPE_3_TRAVEL")
        self.assertEqual(r1.scope, 3)
        self.assertAlmostEqual(float(r1.normalized_quantity), 4023.35)  # 2500 miles -> 4023.35 km
        self.assertEqual(r1.normalized_unit, "km")

    def test_suspicious_record_detection(self):
        """Verify that records with zero quantity, future date, or invalid units are flagged as suspicious."""
        tomorrow = date.today() + timedelta(days=1)
        csv_data = (
            "InvoiceNo,PostingDate,Vendor,FuelType,Quantity,Unit,Cost,PlantCode\n"
            f"INV-001,{tomorrow.strftime('%Y-%m-%d')},QuickGas,Diesel,10.0,gallons,45.0,PL-01\n"  # Future Date
            "INV-002,2026-05-11,QuickGas,Petrol,-5.0,liters,90.0,PL-02\n"                        # Negative Qty
            "INV-003,2026-05-12,QuickGas,Petrol,50.0,unknown_unit,90.0,PL-02\n"                  # Bad Unit
        )
        
        batch = IngestionPipeline.ingest(
            tenant_id=self.tenant.id,
            data_source_id=self.sap_source.id,
            file_name="bad_data.csv",
            file_source=csv_data,
            uploaded_by=self.user
        )
        
        self.assertEqual(batch.status, 'COMPLETED')
        self.assertEqual(batch.total_rows, 3)
        self.assertEqual(batch.processed_rows, 0)
        self.assertEqual(batch.failed_rows, 3)  # All are suspicious
        
        records = EmissionRecord.objects.filter(upload_batch=batch).order_by('transaction_date')
        
        # Verify future date
        r_future = records.get(quantity=10.0)
        self.assertTrue(r_future.suspicious)
        self.assertIn("in the future", "".join(r_future.suspicious_reasons))
        
        # Verify negative quantity
        r_neg = records.get(quantity=-5.0)
        self.assertTrue(r_neg.suspicious)
        self.assertIn("greater than zero", "".join(r_neg.suspicious_reasons))
        
        # Verify unknown unit
        r_unit = records.get(unit="unknown_unit")
        self.assertTrue(r_unit.suspicious)
        self.assertIn("Unit conversion failed", "".join(r_unit.suspicious_reasons))

    def test_outlier_detection(self):
        """Verify that statistical outliers are detected and flagged when batch size is >= 3."""
        csv_data = (
            "InvoiceNo,PostingDate,Vendor,FuelType,Quantity,Unit,Cost,PlantCode\n"
            "INV-001,2026-05-10,QuickGas,Diesel,10.0,liters,45.0,PL-01\n"
            "INV-002,2026-05-11,QuickGas,Diesel,12.0,liters,45.0,PL-01\n"
            "INV-003,2026-05-12,QuickGas,Diesel,11.0,liters,45.0,PL-01\n"
            "INV-004,2026-05-13,QuickGas,Diesel,1000.0,liters,450.0,PL-01\n" # Outlier!
        )
        
        batch = IngestionPipeline.ingest(
            tenant_id=self.tenant.id,
            data_source_id=self.sap_source.id,
            file_name="outlier_data.csv",
            file_source=csv_data,
            uploaded_by=self.user
        )
        
        self.assertEqual(batch.status, 'COMPLETED')
        self.assertEqual(batch.total_rows, 4)
        self.assertEqual(batch.failed_rows, 1)  # Only 1 suspicious (the outlier)
        
        outlier = EmissionRecord.objects.get(upload_batch=batch, quantity=1000.0)
        self.assertTrue(outlier.suspicious)
        self.assertIn("outlier", "".join(outlier.suspicious_reasons))
        
        normal = EmissionRecord.objects.get(upload_batch=batch, quantity=10.0)
        self.assertFalse(normal.suspicious)

    def test_malformed_csv_raises_error_and_updates_batch(self):
        """Verify that a malformed or missing-column CSV fails the ingestion and logs error in UploadBatch."""
        bad_csv = "InvoiceNo,Cost,PlantCode\nINV-01,45.0,PL-01\n"  # Missing critical columns Quantity, Unit, Date
        
        with self.assertRaises(ValidationError):
            IngestionPipeline.ingest(
                tenant_id=self.tenant.id,
                data_source_id=self.sap_source.id,
                file_name="bad_columns.csv",
                file_source=bad_csv,
                uploaded_by=self.user
            )
            
        # Verify the UploadBatch is recorded as FAILED
        batch = UploadBatch.objects.get(file_name="bad_columns.csv")
        self.assertEqual(batch.status, 'FAILED')
        self.assertIn("ValidationError", batch.error_summary)
        
        # Verify transaction safety: no EmissionRecords were saved
        self.assertEqual(EmissionRecord.objects.filter(upload_batch=batch).count(), 0)
