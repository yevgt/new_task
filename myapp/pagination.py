from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Кастомная пагинация с максимум 6 объектами на странице.
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        """
        Кастомный формат ответа с дополнительной информацией.
        """
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.page_size,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'next_page': self.page.next_page_number() if self.page.has_next() else None,
                'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
            },
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'results': data
        })

class CustomLimitOffsetPagination(LimitOffsetPagination):
    """
    Пагинация с использованием limit и offset.
    """
    default_limit = 6
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 50

class CustomCursorPagination(CursorPagination):
    """
    Пагинация с использованием курсора (для больших наборов данных).
    """
    page_size = 6
    ordering = '-created_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    max_page_size = 50