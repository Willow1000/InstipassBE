from rest_framework.pagination import CursorPagination

class StudentCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'