from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Link
from .serializers import LinkSerializer
from .filters import LinkFilter


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Read for authenticated users; write for staff.
    Adjust to your policy (e.g., project members, object-level checks, etc.).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.select_related("content_type").all()
    serializer_class = LinkSerializer
    permission_classes = [IsStaffOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LinkFilter
    search_fields = ("title", "description", "url")
    ordering_fields = ("created_at", "label", "title")
    ordering = ("-created_at",)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs
