"""
Shared pagination classes for the project API.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Default page size for list endpoints.
    Clients may override with ?page_size= up to max_page_size.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
