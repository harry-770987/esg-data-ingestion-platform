from django.contrib import admin
from .models import Tenant, DataSource, UploadBatch, EmissionRecord, AuditLog, ApprovalHistory

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'name', 'source_type', 'is_active')
    list_filter = ('source_type', 'is_active', 'tenant')
    search_fields = ('name', 'description')
    ordering = ('tenant', 'name')


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'data_source', 'file_name', 'status', 'total_rows', 'created_at')
    list_filter = ('status', 'tenant', 'data_source')
    search_fields = ('file_name', 'error_summary')
    readonly_fields = ('total_rows', 'processed_rows', 'failed_rows', 'error_summary', 'created_at')
    ordering = ('-created_at',)


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tenant', 'data_source', 'category', 'activity_type', 
        'transaction_date', 'normalized_quantity', 'normalized_unit', 
        'scope', 'suspicious', 'approved', 'locked'
    )
    list_filter = ('scope', 'category', 'suspicious', 'approved', 'locked', 'tenant', 'data_source')
    search_fields = ('activity_type', 'unit', 'normalized_unit', 'suspicious_reasons')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-transaction_date',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'emission_record', 'changed_by', 'action', 'changed_at')
    list_filter = ('action', 'changed_by')
    readonly_fields = ('emission_record', 'changed_by', 'action', 'previous_values', 'new_values', 'changed_at')
    ordering = ('-changed_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'emission_record', 'reviewed_by', 'action', 'reviewed_at')
    list_filter = ('action', 'reviewed_by')
    readonly_fields = ('emission_record', 'reviewed_by', 'action', 'comments', 'reviewed_at')
    ordering = ('-reviewed_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

