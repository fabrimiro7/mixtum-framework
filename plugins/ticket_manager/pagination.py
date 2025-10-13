from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20                      # default
    page_size_query_param = 'page_size' # override via ?page_size=10
    max_page_size = 100                 # hard cap
