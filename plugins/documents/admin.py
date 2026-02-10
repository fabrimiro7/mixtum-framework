"""
Django admin configuration for the documents plugin.

Registers all models with sensible list_display, search_fields and
list_filter.  Uses TabularInline for template blocks, document blocks
and document signers.
"""

from django.contrib import admin

from .models import (
    Block,
    Document,
    DocumentBlock,
    DocumentCategory,
    DocumentCategoryAssignment,
    DocumentSigner,
    DocumentSignerEvent,
    DocumentStatus,
    DocumentTemplate,
    DocumentTemplateBlock,
    DocumentType,
    Party,
)


# ===================================================================
# Inlines
# ===================================================================

class DocumentTemplateBlockInline(admin.TabularInline):
    model = DocumentTemplateBlock
    extra = 1
    ordering = ("position",)
    fields = ("position", "block", "title_snapshot", "content_snapshot")
    readonly_fields = ("title_snapshot", "content_snapshot")


class DocumentBlockInline(admin.TabularInline):
    model = DocumentBlock
    extra = 0
    ordering = ("position",)
    fields = ("position", "title", "content", "source_template_block")


class DocumentCategoryAssignmentInline(admin.TabularInline):
    model = DocumentCategoryAssignment
    extra = 1
    fields = ("category", "is_primary")


class DocumentSignerInline(admin.TabularInline):
    model = DocumentSigner
    extra = 0
    ordering = ("position",)
    fields = (
        "party",
        "role",
        "position",
        "routing_mode",
        "status",
        "invited_at",
        "signed_at",
    )
    readonly_fields = ("invited_at", "signed_at")


class DocumentSignerEventInline(admin.TabularInline):
    model = DocumentSignerEvent
    extra = 0
    ordering = ("created_at",)
    fields = ("event_type", "ip_address", "created_at", "payload")
    readonly_fields = ("created_at",)


# ===================================================================
# Model Admins
# ===================================================================

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "workspace", "requires_signature", "is_active", "sort_order")
    list_filter = ("is_active", "requires_signature", "workspace")
    search_fields = ("title", "code")
    ordering = ("sort_order", "title")


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "workspace", "parent", "is_active", "sort_order")
    list_filter = ("is_active", "workspace")
    search_fields = ("title", "slug")
    ordering = ("sort_order", "title")


@admin.register(DocumentStatus)
class DocumentStatusAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "workspace", "is_terminal", "sort_order")
    list_filter = ("is_terminal", "workspace")
    search_fields = ("title", "code")
    ordering = ("sort_order",)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "workspace")
    search_fields = ("title", "content")
    ordering = ("title",)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "created_at", "updated_at")
    list_filter = ("workspace",)
    search_fields = ("title", "description")
    inlines = [DocumentTemplateBlockInline]
    ordering = ("title",)


@admin.register(DocumentTemplateBlock)
class DocumentTemplateBlockAdmin(admin.ModelAdmin):
    list_display = ("template", "block", "position", "title_snapshot")
    list_filter = ("template",)
    search_fields = ("title_snapshot",)
    ordering = ("template", "position")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "workspace",
        "type",
        "status",
        "frozen_at",
        "created_at",
    )
    list_filter = ("status", "type", "workspace", "frozen_at")
    search_fields = ("title",)
    readonly_fields = (
        "rendered_html",
        "render_hash",
        "frozen_at",
        "signers_snapshot",
        "created_at",
        "updated_at",
    )
    inlines = [
        DocumentBlockInline,
        DocumentCategoryAssignmentInline,
        DocumentSignerInline,
    ]
    ordering = ("-created_at",)


@admin.register(DocumentBlock)
class DocumentBlockAdmin(admin.ModelAdmin):
    list_display = ("document", "position", "title")
    list_filter = ("document",)
    search_fields = ("title", "content")
    ordering = ("document", "position")


@admin.register(DocumentCategoryAssignment)
class DocumentCategoryAssignmentAdmin(admin.ModelAdmin):
    list_display = ("document", "category", "is_primary")
    list_filter = ("is_primary",)


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "company_name",
        "email",
        "workspace",
        "created_at",
    )
    list_filter = ("workspace",)
    search_fields = ("first_name", "last_name", "company_name", "email", "tax_id")
    ordering = ("last_name", "first_name")


@admin.register(DocumentSigner)
class DocumentSignerAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "party",
        "role",
        "position",
        "routing_mode",
        "status",
    )
    list_filter = ("status", "routing_mode", "role")
    search_fields = ("party__first_name", "party__last_name", "party__email", "role")
    inlines = [DocumentSignerEventInline]
    ordering = ("document", "position")


@admin.register(DocumentSignerEvent)
class DocumentSignerEventAdmin(admin.ModelAdmin):
    list_display = ("document_signer", "event_type", "ip_address", "created_at")
    list_filter = ("event_type",)
    search_fields = ("document_signer__party__email",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
