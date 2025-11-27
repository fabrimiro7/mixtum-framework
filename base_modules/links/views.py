from rest_framework import viewsets, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
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


class ContentTypeLookupView(APIView):
    """
    Returns the ContentType id for a given (app_label, model) pair.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        app_label = request.query_params.get("app_label")
        model = request.query_params.get("model")

        if not app_label or not model:
            return Response(
                {"detail": "app_label e model sono richiesti."},
                status=400
            )

        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            return Response(
                {"detail": "Content type non trovato."},
                status=404
            )

        return Response(
            {
                "id": content_type.id,
                "app_label": content_type.app_label,
                "model": content_type.model,
            }
        )
