"""
Permissions and workspace-scoping utilities for the documents plugin.

`IsWorkspaceMember` is a placeholder that currently allows all authenticated
requests but is wired in so that real workspace-membership checks can be added
later without touching every view.

`WorkspaceMixin` is a viewset mixin that:
  - Extracts the workspace from the ``X-Workspace-Id`` request header.
  - Automatically filters querysets by workspace.
  - Injects the workspace into serializer context and ``perform_create``.
"""

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission

from base_modules.workspace.models import Workspace


class IsWorkspaceMember(BasePermission):
    """
    Placeholder permission class.
    Ensures that the ``X-Workspace-Id`` header is present and refers to an
    existing workspace.  Currently always grants access — future versions will
    check actual membership.
    """

    def has_permission(self, request, view):
        ws_id = request.META.get("HTTP_X_WORKSPACE_ID")
        if not ws_id:
            # Return False so DRF renders a 403; callers that want 400 can
            # handle this in the mixin instead.
            return False
        try:
            int(ws_id)
        except (ValueError, TypeError):
            return False
        # TODO: check actual workspace membership for request.user
        return True


def get_workspace_id_from_request(request) -> int:
    """
    Extract and validate the workspace ID from the X-Workspace-Id header.
    Raises ``ValidationError`` if missing or not a valid integer.
    """
    ws_id = request.META.get("HTTP_X_WORKSPACE_ID")
    if not ws_id:
        raise ValidationError(
            {"detail": "Missing required header X-Workspace-Id."}
        )
    try:
        return int(ws_id)
    except (ValueError, TypeError):
        raise ValidationError(
            {"detail": "X-Workspace-Id must be a valid integer."}
        )


class WorkspaceMixin:
    """
    ViewSet mixin that scopes every query to the workspace identified
    by the ``X-Workspace-Id`` request header.

    Usage::

        class MyViewSet(WorkspaceMixin, ModelViewSet):
            queryset = MyModel.objects.all()
            ...

    The mixin assumes the model has a ``workspace`` or ``workspace_id`` field.
    Override ``workspace_field`` if the FK column has a different name.
    """

    workspace_field: str = "workspace_id"

    def get_workspace_id(self) -> int:
        return get_workspace_id_from_request(self.request)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.workspace_field: self.get_workspace_id()})

    def perform_create(self, serializer):
        serializer.save(**{self.workspace_field: self.get_workspace_id()})

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["workspace_id"] = get_workspace_id_from_request(self.request)
        return ctx
