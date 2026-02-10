"""
Documents plugin models.

Manages document generation (contracts, quotes) using templates, ordered blocks,
dynamic variable rendering, and signer workflows.
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from base_modules.workspace.models import Workspace


# ---------------------------------------------------------------------------
# 1. Core Taxonomy
# ---------------------------------------------------------------------------

class DocumentType(models.Model):
    """
    Configurable document type (e.g. Contract, Quote, NDA).
    Unique per workspace via the `code` slug field.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="document_types",
    )
    code = models.SlugField(
        max_length=100,
        help_text="Slug-like identifier, unique within the workspace.",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    default_template = models.ForeignKey(
        "DocumentTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_types",
    )
    requires_signature = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Document Type"
        verbose_name_plural = "Document Types"
        ordering = ["sort_order", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "code"],
                name="documents_doctype_ws_code_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace", "is_active", "sort_order"],
                name="documents_doctype_ws_active_idx",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.code})"


class DocumentCategory(models.Model):
    """
    Hierarchical document category, unique per workspace via `slug`.
    Supports one level of nesting through the optional `parent` FK.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="document_categories",
    )
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    color = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Optional colour value (e.g. #FF5733).",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"
        ordering = ["sort_order", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "slug"],
                name="documents_doccat_ws_slug_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace", "parent", "sort_order"],
                name="documents_doccat_ws_parent_idx",
            ),
        ]

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# 2. Templates & Blocks
# ---------------------------------------------------------------------------

class Block(models.Model):
    """
    Master block library entry.
    Content may contain Jinja2-style placeholders such as {{ client.first_name }}.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="document_blocks_library",
    )
    title = models.CharField(max_length=255)
    content = models.TextField(
        help_text="Block body — may contain placeholders like {{ client.first_name }}.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Block"
        verbose_name_plural = "Blocks"
        ordering = ["title"]

    def __str__(self):
        return self.title


class DocumentTemplate(models.Model):
    """
    A reusable template composed of ordered blocks (via DocumentTemplateBlock).
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="document_templates",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document Template"
        verbose_name_plural = "Document Templates"
        ordering = ["title"]

    def __str__(self):
        return self.title


class DocumentTemplateBlock(models.Model):
    """
    Ordered association between a DocumentTemplate and a Block.
    Stores a *snapshot* of the block's title and content at the time it was added
    so that later changes to the master block do not affect existing templates.
    """

    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name="template_blocks",
    )
    block = models.ForeignKey(
        Block,
        on_delete=models.PROTECT,
        related_name="template_usages",
    )
    title_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Snapshot of block.title at the time of addition.",
    )
    content_snapshot = models.TextField(
        blank=True,
        default="",
        help_text="Snapshot of block.content at the time of addition.",
    )
    position = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Template Block"
        verbose_name_plural = "Template Blocks"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "position"],
                name="documents_tplblock_tpl_pos_uniq",
            ),
        ]

    def save(self, *args, **kwargs):
        """Auto-populate snapshots from the source block when left empty."""
        if not self.title_snapshot:
            self.title_snapshot = self.block.title
        if not self.content_snapshot:
            self.content_snapshot = self.block.content
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template} — #{self.position} {self.title_snapshot}"


# ---------------------------------------------------------------------------
# 3. Document Status (governed but dynamic)
# ---------------------------------------------------------------------------

class DocumentStatus(models.Model):
    """
    Managed set of statuses for a workspace
    (e.g. draft, finalized, sent_for_signature, signed, archived).
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="document_statuses",
    )
    code = models.SlugField(max_length=100)
    title = models.CharField(max_length=255)
    is_terminal = models.BooleanField(
        default=False,
        help_text="Terminal statuses prevent further editing.",
    )
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Document Status"
        verbose_name_plural = "Document Statuses"
        ordering = ["sort_order", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "code"],
                name="documents_docstatus_ws_code_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.code})"


# ---------------------------------------------------------------------------
# 4. Document Instances
# ---------------------------------------------------------------------------

class Document(models.Model):
    """
    A concrete document instance, optionally created from a template.

    Business rules:
    - Editable while `frozen_at` is NULL and the status is not terminal.
    - `freeze_document()` sets `frozen_at` and persists snapshots.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    status = models.ForeignKey(
        DocumentStatus,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Origin template reference (informational).",
    )
    categories = models.ManyToManyField(
        DocumentCategory,
        through="DocumentCategoryAssignment",
        related_name="documents",
        blank=True,
    )
    context_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Frozen context used for rendering after freeze.",
    )
    signers_snapshot = models.JSONField(
        default=list,
        blank=True,
        help_text="Frozen signers summary after freeze.",
    )
    rendered_html = models.TextField(
        null=True,
        blank=True,
        help_text="Last rendered output.",
    )
    render_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="SHA-256 hash of the rendered HTML.",
    )
    frozen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the document was frozen (immutable after this point).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]

    @property
    def is_editable(self) -> bool:
        """A document is editable if it has not been frozen and its status is not terminal."""
        return self.frozen_at is None and not self.status.is_terminal

    def __str__(self):
        return self.title


class DocumentBlock(models.Model):
    """
    Ordered snapshot block belonging to a Document instance.
    Created by copying from DocumentTemplateBlock or manually.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="blocks",
    )
    source_template_block = models.ForeignKey(
        DocumentTemplateBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_block_instances",
        help_text="Original template block this was copied from (if any).",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    position = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Document Block"
        verbose_name_plural = "Document Blocks"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "position"],
                name="documents_docblock_doc_pos_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.document} — #{self.position} {self.title}"


class DocumentCategoryAssignment(models.Model):
    """
    Through model for Document <-> DocumentCategory M2M.
    Allows marking one category as primary per document.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="category_assignments",
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.CASCADE,
        related_name="document_assignments",
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Document Category Assignment"
        verbose_name_plural = "Document Category Assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["document", "category"],
                name="documents_catassign_doc_cat_uniq",
            ),
        ]

    def clean(self):
        """Enforce at most one primary category per document."""
        if self.is_primary:
            qs = DocumentCategoryAssignment.objects.filter(
                document=self.document,
                is_primary=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "A document can only have one primary category."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        primary = " [PRIMARY]" if self.is_primary else ""
        return f"{self.document} — {self.category}{primary}"


# ---------------------------------------------------------------------------
# 5. Signers
# ---------------------------------------------------------------------------

class Party(models.Model):
    """
    A person or entity that can sign documents.
    May be internal (user_id set) or external (identified by email/phone).
    `user_id` is a loose-coupling UUID field — it does NOT create a FK to the auth user model.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="document_parties",
    )
    user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of the auth user (loose coupling — not a FK).",
    )
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    company_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(blank=True, default="", db_index=True)
    phone = models.CharField(max_length=50, blank=True, default="")
    tax_id = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Party"
        verbose_name_plural = "Parties"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        parts = []
        if self.first_name or self.last_name:
            parts.append(f"{self.first_name} {self.last_name}".strip())
        if self.company_name:
            parts.append(self.company_name)
        return " — ".join(parts) or self.email or str(self.pk)


ROUTING_MODE_CHOICES = [
    ("parallel", "Parallel"),
    ("sequential", "Sequential"),
]

SIGNER_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("invited", "Invited"),
    ("viewed", "Viewed"),
    ("signed", "Signed"),
    ("rejected", "Rejected"),
    ("expired", "Expired"),
]


class DocumentSigner(models.Model):
    """
    Links a Party to a Document with a specific role and signing workflow.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="signers",
    )
    party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="signer_roles",
    )
    role = models.CharField(
        max_length=100,
        help_text="e.g. client, provider, witness",
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="Signing order (relevant when routing_mode is sequential).",
    )
    routing_mode = models.CharField(
        max_length=20,
        choices=ROUTING_MODE_CHOICES,
        default="parallel",
    )
    status = models.CharField(
        max_length=20,
        choices=SIGNER_STATUS_CHOICES,
        default="draft",
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    signature_method = models.CharField(max_length=100, blank=True, default="")
    provider_envelope_id = models.CharField(max_length=255, blank=True, default="")
    provider_signer_id = models.CharField(max_length=255, blank=True, default="")
    magic_link_token_hash = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Document Signer"
        verbose_name_plural = "Document Signers"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "party", "role"],
                name="documents_signer_doc_party_role_uniq",
            ),
        ]

    def clean(self):
        """
        When routing_mode is sequential, enforce unique position per document.
        (Parallel signers may share the same position.)
        """
        if self.routing_mode == "sequential":
            qs = DocumentSigner.objects.filter(
                document=self.document,
                position=self.position,
                routing_mode="sequential",
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Sequential signers must have unique positions within a document."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.party} as {self.role} on {self.document}"


SIGNER_EVENT_TYPES = [
    ("INVITED", "Invited"),
    ("OPENED", "Opened"),
    ("OTP_SENT", "OTP Sent"),
    ("SIGNED", "Signed"),
    ("REJECTED", "Rejected"),
    ("EXPIRED", "Expired"),
    ("REMINDER_SENT", "Reminder Sent"),
]


class DocumentSignerEvent(models.Model):
    """
    Audit trail for signer-related events (invited, opened, signed, etc.).
    """

    document_signer = models.ForeignKey(
        DocumentSigner,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=50,
        choices=SIGNER_EVENT_TYPES,
        help_text="e.g. INVITED, OPENED, SIGNED, REJECTED",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Signer Event"
        verbose_name_plural = "Signer Events"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.event_type} — {self.document_signer} @ {self.created_at}"
