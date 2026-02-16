from django.contrib import admin
from .models import BrandingSettings


@admin.register(BrandingSettings)
class BrandingSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "workspace", "updated_at")
    list_filter = ("workspace",)
    search_fields = ("workspace__workspace_name",)
