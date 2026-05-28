import uuid
import io
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import date
from core.models import Tenant, DataSource, UploadBatch, EmissionRecord, AuditLog, ApprovalHistory

class ESGAPITestCase(APITestCase):
    def setUp(self):
        # Create Tenants
        self.tenant_a = Tenant.objects.create(name="Tenant Alpha Corp")
        self.tenant_b = Tenant.objects.create(name="Tenant Beta Corp")
        
        # Create Users
        self.user = User.objects.create_user(username="auditor", password="password123")
        self.client.force_authenticate(user=self.user)

        # Create Data Sources
        self.source_a = DataSource.objects.create(
            tenant=self.tenant_a,
            name="SAP Fuel A",
            source_type="SAP_FUEL"
        )
        self.source_b = DataSource.objects.create(
            tenant=self.tenant_b,
            name="SAP Fuel B",
            source_type="SAP_FUEL"
        )

        # Create a sample batch and record for Tenant A
        self.batch_a = UploadBatch.objects.create(
            tenant=self.tenant_a,
            data_source=self.source_a,
            file_name="alpha_logs.csv",
            status="COMPLETED"
        )
        self.record_a = EmissionRecord.objects.create(
            tenant=self.tenant_a,
            data_source=self.source_a,
            upload_batch=self.batch_a,
            category="SCOPE_1_FUEL",
            activity_type="Diesel",
            transaction_date=date(2026, 5, 1),
            quantity=100.0,
            unit="gallons",
            normalized_quantity=378.541,
            normalized_unit="L",
            scope=1,
            suspicious=False,
            approved=False,
            locked=False
        )

        # Create a sample batch and record for Tenant B
        self.batch_b = UploadBatch.objects.create(
            tenant=self.tenant_b,
            data_source=self.source_b,
            file_name="beta_logs.csv",
            status="COMPLETED"
        )
        self.record_b = EmissionRecord.objects.create(
            tenant=self.tenant_b,
            data_source=self.source_b,
            upload_batch=self.batch_b,
            category="SCOPE_1_FUEL",
            activity_type="Petrol",
            transaction_date=date(2026, 5, 2),
            quantity=50.0,
            unit="liters",
            normalized_quantity=50.0,
            normalized_unit="L",
            scope=1,
            suspicious=False,
            approved=False,
            locked=False
        )

        # URL endpoints
        self.status_url = reverse('api:status')
        self.records_url = reverse('api:record-list')
        self.batches_url = reverse('api:batch-list')
        self.upload_url = reverse('api:batch-upload')
        self.audit_url = reverse('api:auditlog-list')

    def test_health_check_public(self):
        """Verify the health check is accessible without headers."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'online')

    def test_tenant_header_requirement(self):
        """Verify that requests to protected endpoints fail without tenant header."""
        response = self.client.get(self.records_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("X-Tenant-ID header is required", response.data['detail'])

    def test_tenant_isolation(self):
        """Verify Tenant A only sees Tenant A's records and batches, not Tenant B's."""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant_a.id))
        
        # 1. Fetch records
        response = self.client.get(self.records_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.record_a.id))

        # 2. Try to fetch Tenant B's record detail directly
        detail_url = reverse('api:record-detail', kwargs={'pk': self.record_b.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_csv_upload_api(self):
        """Verify CSV uploads trigger pipeline and correctly return results."""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant_a.id))
        
        csv_content = (
            "InvoiceNo,PostingDate,Vendor,FuelType,Quantity,Unit,Cost,PlantCode\n"
            "INV-100,2026-05-15,AcmeFuel,Diesel,20.0,gallons,80.0,PL-01\n"
        )
        csv_file = SimpleUploadedFile("sap_upload.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        response = self.client.post(self.upload_url, {
            'file': csv_file,
            'source_type': 'SAP_FUEL'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'COMPLETED')
        self.assertEqual(response.data['total_rows'], 1)
        self.assertEqual(response.data['processed_rows'], 1)
        self.assertEqual(response.data['failed_rows'], 0)

    def test_record_filtering_and_search(self):
        """Verify filters and search parameters are correctly processed."""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant_a.id))
        
        # Create a suspicious record for testing
        EmissionRecord.objects.create(
            tenant=self.tenant_a,
            data_source=self.source_a,
            upload_batch=self.batch_a,
            category="SCOPE_1_FUEL",
            activity_type="Outlier Gas",
            transaction_date=date(2026, 5, 3),
            quantity=-10.0, # Negative makes it suspicious
            unit="liters",
            normalized_quantity=None,
            normalized_unit="L",
            scope=1,
            suspicious=True,
            suspicious_reasons=["Quantity must be greater than zero"]
        )

        # Filter by suspicious=true
        response = self.client.get(self.records_url, {'suspicious': 'true'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['activity_type'], "Outlier Gas")

        # Search activity type (case-insensitive substring)
        response = self.client.get(self.records_url, {'activity_type': 'outlier'})
        self.assertEqual(response.data['count'], 1)

    def test_edit_record_generates_audit_log(self):
        """Verify editing a record recomputes normalization and creates an AuditLog."""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant_a.id))
        
        detail_url = reverse('api:record-detail', kwargs={'pk': self.record_a.id})
        
        # Edit quantity (gallons)
        response = self.client.patch(detail_url, {'quantity': 20.0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check recomputed normalized quantity (20 gallons -> 75.7082 L)
        self.assertAlmostEqual(float(response.data['normalized_quantity']), 75.7082)
        
        # Verify AuditLog was automatically created
        audit_logs = AuditLog.objects.filter(emission_record=self.record_a)
        self.assertEqual(audit_logs.count(), 1)
        log = audit_logs.first()
        self.assertEqual(log.action, 'EDIT')
        self.assertEqual(float(log.previous_values['quantity']), 100.0)
        self.assertEqual(float(log.new_values['quantity']), 20.0)

    def test_locked_record_protection(self):
        """Verify editing or approving a locked record returns 403 Forbidden."""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant_a.id))
        
        # Lock the record
        self.record_a.locked = True
        self.record_a.save()

        detail_url = reverse('api:record-detail', kwargs={'pk': self.record_a.id})
        approve_url = reverse('api:record-approve', kwargs={'pk': self.record_a.id})

        # Try PATCH
        response = self.client.patch(detail_url, {'quantity': 30.0})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try POST to approve
        response = self.client.post(approve_url, {'comments': 'Let me approve'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approval_workflow_locks_record(self):
        """Verify that approving a record updates status, logs actions, and locks the record."""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant_a.id))
        
        approve_url = reverse('api:record-approve', kwargs={'pk': self.record_a.id})
        response = self.client.post(approve_url, {'comments': 'Verified correct'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approved'])
        self.assertTrue(response.data['locked'])

        # Verify history logs
        self.assertTrue(ApprovalHistory.objects.filter(emission_record=self.record_a, action='APPROVE').exists())
        self.assertTrue(AuditLog.objects.filter(emission_record=self.record_a, action='LOCK').exists())
