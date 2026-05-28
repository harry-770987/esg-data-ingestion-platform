import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Tenant(models.Model):
    """
    Represents an isolated organization, company, or corporate client.
    Ensures complete logical isolation of data for multi-tenancy.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DataSource(models.Model):
    """
    Represents a system or connection from which ESG data originates.
    E.g. "SAP Fuel/Procurement Export", "PG&E Electricity Portal", "Concur Corporate Travel".
    """
    SOURCE_TYPES = [
        ('SAP_FUEL', 'SAP Fuel Procurement'),
        ('UTILITY_ELEC', 'Utility Electricity'),
        ('TRAVEL_CORP', 'Corporate Travel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_sources')
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return f"{self.tenant.name} - {self.name} ({self.get_source_type_display()})"


class UploadBatch(models.Model):
    """
    Tracks a single CSV ingestion execution. Allows traceability and bulk actions 
    (e.g., deleting/rolling back a batch if the data was corrupted).
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='upload_batches')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='upload_batches')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.file_name} ({self.status}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class EmissionRecord(models.Model):
    """
    The unified emission records table. Contains the normalized physical parameters 
    required to compute carbon output and perform audit reviews.
    """
    CATEGORIES = [
        ('SCOPE_1_FUEL', 'Scope 1 Fuel'),
        ('SCOPE_2_ELEC', 'Scope 2 Electricity'),
        ('SCOPE_3_TRAVEL', 'Scope 3 Travel'),
    ]

    SCOPE_CHOICES = [
        (1, 'Scope 1'),
        (2, 'Scope 2'),
        (3, 'Scope 3'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='emission_records')
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='emission_records')
    upload_batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name='emission_records')
    
    category = models.CharField(max_length=50, choices=CATEGORIES)
    activity_type = models.CharField(max_length=100) # e.g. "Diesel", "Electricity", "Flight"
    transaction_date = models.DateField() # The date the carbon-emitting event occurred
    
    # Raw ingestion values
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=50) # e.g. "gallons", "MWh", "miles"
    
    # Normalized parameters
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    normalized_unit = models.CharField(max_length=50, null=True, blank=True) # e.g. "L", "kWh", "km"
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    
    # Validation & workflows
    suspicious = models.BooleanField(default=False)
    suspicious_reasons = models.JSONField(default=list, blank=True) # List of string validation failures
    
    approved = models.BooleanField(default=False)
    locked = models.BooleanField(default=False) # Once locked, data changes are barred
    
    raw_data = models.JSONField(default=dict) # Complete original CSV row dictionary
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validate record state. Specifically enforces audit locking.
        """
        if self.pk:
            try:
                original = EmissionRecord.objects.get(pk=self.pk)
            except EmissionRecord.DoesNotExist:
                # The record is being created, so no edit locking logic applies
                return

            # If the record was locked, and remains locked, we reject any modifications
            # to physical or audit-critical fields.
            if original.locked and self.locked:
                for field in self._meta.fields:
                    field_name = field.name
                    # Allow changes to lock/approve state during an unlock event, but block data changes
                    if field_name not in ['locked', 'approved', 'updated_at']:
                        if getattr(original, field_name) != getattr(self, field_name):
                            raise ValidationError(
                                f"Field '{field_name}' cannot be modified because the record is locked for audit."
                            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.activity_type}: {self.normalized_quantity} {self.normalized_unit} ({self.transaction_date})"


class AuditLog(models.Model):
    """
    Immutable ledger tracking edits to physical fields of EmissionRecord by analysts.
    """
    ACTIONS = [
        ('CREATE', 'Record Created'),
        ('EDIT', 'Record Edited'),
        ('LOCK', 'Record Locked'),
        ('UNLOCK', 'Record Unlocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emission_record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=ACTIONS)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.action} on {self.emission_record.id} by {self.changed_by} at {self.changed_at.strftime('%Y-%m-%d %H:%M')}"


class ApprovalHistory(models.Model):
    """
    Workflow record tracking comments, timestamps, and actions during the review phase.
    """
    ACTIONS = [
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emission_record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='approval_history')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=ACTIONS)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} on {self.emission_record.id} by {self.reviewed_by}"
