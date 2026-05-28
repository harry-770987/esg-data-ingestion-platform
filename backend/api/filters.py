import django_filters
from core.models import EmissionRecord

class EmissionRecordFilter(django_filters.FilterSet):
    """
    Filter set to perform advanced querying on EmissionRecord endpoints.
    Supports filtering by dates, source type, scope, suspension flags, and activity type search.
    """
    start_date = django_filters.DateFilter(field_name='transaction_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='transaction_date', lookup_expr='lte')
    activity_type = django_filters.CharFilter(field_name='activity_type', lookup_expr='icontains')
    source_type = django_filters.CharFilter(field_name='data_source__source_type', lookup_expr='exact')

    class Meta:
        model = EmissionRecord
        fields = {
            'scope': ['exact'],
            'suspicious': ['exact'],
            'approved': ['exact'],
            'locked': ['exact'],
            'upload_batch': ['exact'],
            'category': ['exact']
        }
