from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from base_modules.workspace.models import Workspace
from .constants import DEFAULT_COLORS
from .models import BrandingSettings
from .serializers import BrandingSettingsSerializer


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        return getattr(user, "permission", 0) == 100


def _file_url(request, file_field):
    if not file_field:
        return None
    try:
        url = file_field.url
    except ValueError:
        return None
    return request.build_absolute_uri(url) if request else url


class GlobalBrandingView(APIView):
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get(self, request):
        instance = BrandingSettings.objects.filter(workspace__isnull=True).order_by("id").first()
        if not instance:
            return Response(
                {
                    "workspace": None,
                    "colors": {},
                    "logo_full": None,
                    "logo_compact": None,
                    "favicon": None,
                }
            )
        serializer = BrandingSettingsSerializer(instance, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        instance = BrandingSettings.objects.filter(workspace__isnull=True).order_by("id").first()
        if not instance:
            instance = BrandingSettings.objects.create()
        serializer = BrandingSettingsSerializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class WorkspaceBrandingView(APIView):
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get(self, request, workspace_id: int):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        instance = BrandingSettings.objects.filter(workspace=workspace).first()
        if not instance:
            return Response(
                {
                    "workspace": workspace.id,
                    "colors": {},
                    "logo_full": None,
                    "logo_compact": None,
                    "favicon": None,
                }
            )
        serializer = BrandingSettingsSerializer(instance, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, workspace_id: int):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        instance, _created = BrandingSettings.objects.get_or_create(workspace=workspace)
        serializer = BrandingSettingsSerializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EffectiveBrandingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        workspace_id_raw = request.query_params.get("workspace_id")
        try:
            workspace_id = int(workspace_id_raw) if workspace_id_raw else None
        except (TypeError, ValueError):
            workspace_id = None
        colors = {**DEFAULT_COLORS}

        global_settings = BrandingSettings.objects.filter(workspace__isnull=True).order_by("id").first()
        if global_settings and global_settings.colors:
            colors.update(global_settings.colors)

        workspace_settings = None
        if workspace_id:
            workspace_settings = BrandingSettings.objects.filter(workspace_id=workspace_id).first()
            if workspace_settings and workspace_settings.colors:
                colors.update(workspace_settings.colors)

        logo_full = (
            workspace_settings.logo_full if workspace_settings and workspace_settings.logo_full else None
        ) or (global_settings.logo_full if global_settings else None)
        logo_compact = (
            workspace_settings.logo_compact if workspace_settings and workspace_settings.logo_compact else None
        ) or (global_settings.logo_compact if global_settings else None)
        favicon = (
            workspace_settings.favicon if workspace_settings and workspace_settings.favicon else None
        ) or (global_settings.favicon if global_settings else None)

        return Response(
            {
                "workspace_id": workspace_id,
                "colors": colors,
                "logo_full": _file_url(request, logo_full),
                "logo_compact": _file_url(request, logo_compact),
                "favicon": _file_url(request, favicon),
            }
        )
