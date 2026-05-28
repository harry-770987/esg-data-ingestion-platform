from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import api_status, UploadBatchViewSet, EmissionRecordViewSet, AuditLogViewSet

app_name = 'api'

# Setup DRF Router
router = DefaultRouter()
router.register(r'batches', UploadBatchViewSet, basename='batch')
router.register(r'records', EmissionRecordViewSet, basename='record')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('status/', api_status, name='status'),
    path('', include(router.urls)),
]
