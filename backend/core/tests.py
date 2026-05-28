from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date
from .models import Tenant, DataSource, UploadBatch, EmissionRecord, AuditLog, ApprovalHistory

class ESGModelTestCase(TestCase):
    def setUp(self):
        # Create a test tenant
        self.tenant = Tenant.objects.create(name="Test Organization Corp")
        
        # Create a test user
        self.user = User.objects.create_user(username="analyst", password="password123")
        
        # Create a data source
        self.data_source = DataSource.objects.create(
            tenant=self.tenant,
            name="SAP Fuel Export",
            source_type="SAP_FUEL",
            description="SAP fuel procurement logs for Scope 1"
        )
        
        # Create an upload batch
        self.batch = UploadBatch.objects.create(
            tenant=self.tenant,
            data_source=self.data_source,
            uploaded_by=self.user,
            file_name="sap_q1_2026.csv",
            status="COMPLETED",
            total_rows=10,
            processed_rows=10,
            failed_rows=0
        )

    def test_tenant_creation(self):
        """Verify Tenant model can be created and has UUID id."""
        self.assertIsNotNone(self.tenant.id)
        self.assertEqual(str(self.tenant), "Test Organization Corp")

    def test_data_source_uniqueness(self):
        """Verify that a Tenant cannot have duplicate DataSource names."""
        with self.assertRaises(Exception):
            DataSource.objects.create(
                tenant=self.tenant,
                name="SAP Fuel Export",  # Duplicate name
                source_type="UTILITY_ELEC"
            )

    def test_emission_record_creation(self):
        """Verify EmissionRecord can be created and normalized correctly."""
        record = EmissionRecord.objects.create(
            tenant=self.tenant,
            data_source=self.data_source,
            upload_batch=self.batch,
            category="SCOPE_1_FUEL",
            activity_type="Diesel",
            transaction_date=date(2026, 5, 1),
            quantity=100.0,
            unit="gallons",
            normalized_quantity=378.541,
            normalized_unit="L",
            scope=1,
            raw_data={"InvoiceNo": "INV-123", "Quantity": "100", "Unit": "gallons"}
        )
        self.assertIsNotNone(record.id)
        self.assertEqual(record.scope, 1)
        self.assertFalse(record.locked)
        self.assertFalse(record.approved)

    def test_audit_locking_enforcement(self):
        """Verify that locked emission records reject edits to data fields, but allow unlocking."""
        record = EmissionRecord.objects.create(
            tenant=self.tenant,
            data_source=self.data_source,
            upload_batch=self.batch,
            category="SCOPE_1_FUEL",
            activity_type="Diesel",
            transaction_date=date(2026, 5, 1),
            quantity=100.0,
            unit="gallons",
            normalized_quantity=378.541,
            normalized_unit="L",
            scope=1,
            locked=True  # Initially locked
        )

        # Modifying a data field should fail validation
        record.quantity = 150.0
        with self.assertRaises(ValidationError):
            record.save()

        # Reload from DB and try changing activity_type
        record = EmissionRecord.objects.get(pk=record.pk)
        record.activity_type = "Petrol"
        with self.assertRaises(ValidationError):
            record.save()

        # Changing only the locked state to False (unlocking) should succeed
        record = EmissionRecord.objects.get(pk=record.pk)
        record.locked = False
        record.save()  # Should succeed
        
        # Now that it's unlocked, editing physical fields should succeed
        record.quantity = 150.0
        record.save()
        self.assertEqual(EmissionRecord.objects.get(pk=record.pk).quantity, 150.0)

