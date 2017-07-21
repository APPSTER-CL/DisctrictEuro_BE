from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PageNumberPagination2(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('page_size', self.page_size),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


def paginated_by(*args, **kwargs):
    new_page_size = kwargs.pop('page_size', 100)

    class InnerPaginator(PageNumberPagination2):
        page_size = new_page_size

    return InnerPaginator
