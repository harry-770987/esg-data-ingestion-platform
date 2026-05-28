from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for API querysets. Defaults to 25 items per page, 
    but permits clients to request custom sizes up to 100 items.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
