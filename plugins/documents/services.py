"""
Business logic services for the documents plugin.

Provides:
- Sandboxed Jinja2 environment for safe template rendering
- Document creation from templates (with block snapshot copying)
- Document rendering with context variable interpolation
- Document freezing with signer snapshot persistence
"""

import hashlib
import logging
from datetime import date, datetime
from typing import Optional

from django.db import transaction as db_transaction
from django.utils import timezone

from jinja2 import BaseLoader
from jinja2.sandbox import SandboxedEnvironment

from .models import (
    Document,
    DocumentBlock,
    DocumentCategoryAssignment,
    DocumentSigner,
    DocumentStatus,
    DocumentTemplate,
    DocumentTemplateBlock,
    DocumentType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Jinja2 Sandboxed Environment
# ---------------------------------------------------------------------------

def _dateformat(value, fmt: str = "%Y-%m-%d") -> str:
    """
    Custom Jinja2 filter to format dates.
    Accepts date/datetime objects or ISO-format strings.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value
    if isinstance(value, (date, datetime)):
        return value.strftime(fmt)
    return str(value)


def safe_jinja_environment() -> SandboxedEnvironment:
    """
    Return a Jinja2 SandboxedEnvironment with a restricted set of filters.
    Only allows dict-like context access (no arbitrary attribute access).
    """
    env = SandboxedEnvironment(
        loader=BaseLoader(),
        autoescape=False,
        # Keep default undefined behaviour (raises on missing keys)
    )

    # Restrict available filters to a safe whitelist
    allowed_filters = {
        "upper": str.upper,
        "lower": str.lower,
        "title": str.title,
        "default": lambda value, default_value="": value if value else default_value,
        "replace": lambda value, old, new: str(value).replace(old, new),
        "dateformat": _dateformat,
    }
    env.filters = allowed_filters
    return env


# ---------------------------------------------------------------------------
# Service: create document from template
# ---------------------------------------------------------------------------

def create_document_from_template(
    *,
    workspace_id: int,
    title: str,
    type_id: int,
    template_id: int,
    status_code: str = "draft",
    context: Optional[dict] = None,
    category_ids: Optional[list[int]] = None,
) -> Document:
    """
    Create a new Document by copying blocks from a DocumentTemplate.

    Steps:
    1. Resolve workspace, type, template and initial status.
    2. Create the Document record.
    3. Copy every DocumentTemplateBlock into a DocumentBlock (preserving order
       and snapshot content).
    4. Optionally set context_snapshot and attach categories.

    Returns the created Document instance.
    """
    with db_transaction.atomic():
        status = DocumentStatus.objects.get(
            workspace_id=workspace_id,
            code=status_code,
        )
        doc_type = DocumentType.objects.get(pk=type_id)
        template = DocumentTemplate.objects.get(pk=template_id)

        document = Document.objects.create(
            workspace_id=workspace_id,
            title=title,
            status=status,
            type=doc_type,
            template=template,
            context_snapshot=context or {},
        )

        # Copy template blocks → document blocks
        template_blocks = (
            DocumentTemplateBlock.objects
            .filter(template=template)
            .select_related("block")
            .order_by("position")
        )

        doc_blocks = [
            DocumentBlock(
                document=document,
                source_template_block=tb,
                title=tb.title_snapshot,
                content=tb.content_snapshot,
                position=tb.position,
            )
            for tb in template_blocks
        ]
        DocumentBlock.objects.bulk_create(doc_blocks)

        # Attach categories
        if category_ids:
            assignments = [
                DocumentCategoryAssignment(
                    document=document,
                    category_id=cat_id,
                    is_primary=(i == 0),  # first category is primary by default
                )
                for i, cat_id in enumerate(category_ids)
            ]
            DocumentCategoryAssignment.objects.bulk_create(assignments)

    return document


# ---------------------------------------------------------------------------
# Service: render document
# ---------------------------------------------------------------------------

def render_document(
    *,
    document: Document,
    context_override: Optional[dict] = None,
) -> str:
    """
    Render every DocumentBlock.content using Jinja2, concatenate, and persist.

    Context resolution:
    - If the document is frozen → use context_snapshot only (override ignored).
    - Otherwise → merge context_snapshot with context_override (override wins).

    The rendered HTML is stored on `document.rendered_html` and a SHA-256 hash
    is stored on `document.render_hash`.

    Returns the rendered HTML string.
    """
    # Build rendering context
    if document.frozen_at is not None:
        context = document.context_snapshot or {}
    else:
        context = dict(document.context_snapshot or {})
        if context_override:
            context.update(context_override)

    env = safe_jinja_environment()

    blocks = document.blocks.order_by("position")
    rendered_parts: list[str] = []

    for block in blocks:
        try:
            tpl = env.from_string(block.content)
            rendered_content = tpl.render(**context)
        except Exception:
            logger.exception(
                "Error rendering block %s (position %s) of document %s",
                block.pk,
                block.position,
                document.pk,
            )
            rendered_content = block.content  # fallback to raw content

        rendered_parts.append(
            f'<div data-block="{block.pk}" data-position="{block.position}">'
            f"{rendered_content}"
            f"</div>"
        )

    rendered_html = "\n".join(rendered_parts)
    render_hash = hashlib.sha256(rendered_html.encode("utf-8")).hexdigest()

    document.rendered_html = rendered_html
    document.render_hash = render_hash
    document.save(update_fields=["rendered_html", "render_hash", "updated_at"])

    return rendered_html


# ---------------------------------------------------------------------------
# Service: freeze document
# ---------------------------------------------------------------------------

def freeze_document(*, document: Document) -> Document:
    """
    Freeze a document, making it immutable.

    Steps:
    1. Set `frozen_at` to now.
    2. Snapshot current signers into `signers_snapshot`.
    3. Trigger a final render (if context is available).
    """
    now = timezone.now()

    # Build signers snapshot
    signers = (
        DocumentSigner.objects
        .filter(document=document)
        .select_related("party")
        .order_by("position")
    )
    signers_data = [
        {
            "signer_id": signer.pk,
            "party_id": signer.party_id,
            "party_name": str(signer.party),
            "party_email": signer.party.email,
            "role": signer.role,
            "position": signer.position,
            "routing_mode": signer.routing_mode,
            "status": signer.status,
            "invited_at": signer.invited_at.isoformat() if signer.invited_at else None,
            "signed_at": signer.signed_at.isoformat() if signer.signed_at else None,
        }
        for signer in signers
    ]

    document.frozen_at = now
    document.signers_snapshot = signers_data
    document.save(
        update_fields=["frozen_at", "signers_snapshot", "updated_at"],
    )

    # Final render (uses frozen context)
    if document.context_snapshot:
        render_document(document=document)

    return document
