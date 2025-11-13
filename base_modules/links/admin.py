from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Link


class LinkInline(GenericTabularInline):
    """
    Reusable inline: import and attach to any target admin to manage links inline.
    Example:
        from links.admin import LinkInline
        @admin.register(Project)
        class ProjectAdmin(admin.ModelAdmin):
            inlines = [LinkInline]
    """
    model = Link
    extra = 1
    fields = ("label", "title", "url", "description",)
    autocomplete_fields = ()
    show_change_link = True


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("title", "label", "url", "short_target", "created_at")
    list_filter = ("label", "content_type", "created_at")
    search_fields = ("title", "description", "url")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Link", {"fields": ("label", "title", "url", "description")}),
        ("Target", {"fields": ("content_type", "object_id")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )
