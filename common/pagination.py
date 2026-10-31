import math

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            size = self.get_page_size(request) or self.page_size
            total = max(1, math.ceil(queryset.count() / size))
            raise NotFound(f"Noto'g'ri sahifa raqami. Mavjud sahifalar: 1 dan {total} gacha.")

    def get_paginated_response(self, data):
        paginator = self.page.paginator
        return Response(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": self.page.number,
                "page_size": paginator.per_page,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "example": 45},
                "total_pages": {"type": "integer", "example": 5},
                "current_page": {"type": "integer", "example": 2},
                "page_size": {"type": "integer", "example": 10},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "results": schema,
            },
        }
