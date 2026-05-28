from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Tenant, DataSource, UploadBatch, EmissionRecord, AuditLog, ApprovalHistory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'created_at']


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ['id', 'tenant', 'name', 'source_type', 'description', 'is_active']
        read_only_fields = ['id', 'tenant']


class UploadBatchSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)

    class Meta:
        model = UploadBatch
        fields = [
            'id', 'tenant', 'data_source', 'data_source_name', 'uploaded_by', 
            'file_name', 'status', 'total_rows', 'processed_rows', 
            'failed_rows', 'error_summary', 'created_at'
        ]
        read_only_fields = fields


class EmissionRecordSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            'id', 'tenant', 'data_source', 'data_source_name', 'upload_batch',
            'category', 'activity_type', 'transaction_date', 'quantity', 'unit',
            'normalized_quantity', 'normalized_unit', 'scope', 'suspicious',
            'suspicious_reasons', 'approved', 'locked', 'raw_data',
            'created_at', 'updated_at'
        ]
        # Physically critical fields are editable prior to approval/lock.
        # System parameters derived from pipeline are read_only.
        read_only_fields = [
            'id', 'tenant', 'data_source', 'upload_batch', 'category', 
            'normalized_quantity', 'normalized_unit', 'scope', 'suspicious', 
            'suspicious_reasons', 'approved', 'locked', 'raw_data', 
            'created_at', 'updated_at'
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'emission_record', 'changed_by', 'changed_at', 
            'action', 'previous_values', 'new_values'
        ]
        read_only_fields = fields


class ApprovalHistorySerializer(serializers.ModelSerializer):
    reviewed_by = UserSerializer(read_only=True)

    class Meta:
        model = ApprovalHistory
        fields = ['id', 'emission_record', 'reviewed_by', 'reviewed_at', 'action', 'comments']
        read_only_fields = fields
