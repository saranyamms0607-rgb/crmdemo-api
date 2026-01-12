from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LeadPagination(PageNumberPagination):
    page_size = 10                     # default items per page
    page_size_query_param = "page_size"  # ?page_size=20
    max_page_size = 100                # safety limit
    page_query_param = "page"          # ?page=2

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            **data
        })

