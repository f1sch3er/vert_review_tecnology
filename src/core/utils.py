from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class PaginationClass(PageNumberPagination):
    page_size = 5      
    page_size_query_param = 'limit'  
    max_page_size = 100 

    def get_paginated_response(self, data):
        """
        Retorna apenas o array de dados para manter a compatibilidade com o front-end.
        """
        return Response(data)