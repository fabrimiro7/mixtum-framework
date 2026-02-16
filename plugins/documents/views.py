"""
DRF ViewSets for the documents plugin.

Every viewset uses ``WorkspaceMixin`` to scope queries by the workspace
identified in the ``X-Workspace-Id`` request header.

Custom actions:
- DocumentTemplateViewSet: add_block, reorder
- DocumentViewSet: from_template, render, freeze, reorder_blocks
- DocumentSignerViewSet: create_event
"""

from django.db import transaction as db_transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import (
    Block,
    Document,
    DocumentBlock,
    DocumentCategory,
    DocumentSigner,
    DocumentSignerEvent,
    DocumentStatus,
    DocumentTemplate,
    DocumentTemplateBlock,
    DocumentType,
    Party,
)
from .permissions import IsWorkspaceMember, WorkspaceMixin
from .serializers import (
    BlockSerializer,
    CreateDocumentFromTemplateSerializer,
    DocumentBlockSerializer,
    DocumentBlockWriteSerializer,
    DocumentCategorySerializer,
    DocumentSerializer,
    DocumentSignerEventSerializer,
    DocumentSignerSerializer,
    DocumentSignerWriteSerializer,
    DocumentStatusSerializer,
    DocumentTemplateBlockSerializer,
    DocumentTemplateBlockWriteSerializer,
    DocumentTemplateSerializer,
    DocumentTemplateWriteSerializer,
    DocumentTypeSerializer,
    DocumentWriteSerializer,
    PartySerializer,
    RenderDocumentSerializer,
    ReorderSerializer,
)
from .services import (
    create_document_from_template,
    freeze_document,
    render_document,
)
from .permissions import get_workspace_id_from_request


# ===================================================================
# Core Taxonomy
# ===================================================================

class DocumentTypeViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """CRUD for document types."""

    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    #permission_classes = [IsWorkspaceMember]


class DocumentCategoryViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """CRUD for document categories."""

    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    #permission_classes = [IsWorkspaceMember]


class DocumentStatusViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """
    CRUD for document statuses.

    NOTE: This model is "governed" — in production you may want to restrict
    writes to admin users or a specific permission.
    """

    queryset = DocumentStatus.objects.all()
    serializer_class = DocumentStatusSerializer
    #permission_classes = [IsWorkspaceMember]


# ===================================================================
# Blocks & Templates
# ===================================================================

class BlockViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """CRUD for master block library."""

    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    #permission_classes = [IsWorkspaceMember]


class DocumentTemplateViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """
    CRUD for document templates.

    Extra actions:
    - POST   /templates/{id}/blocks/   — add a block at a position
    - PATCH  /templates/{id}/reorder/  — reorder template blocks
    """

    queryset = DocumentTemplate.objects.prefetch_related("template_blocks__block")
    #permission_classes = [IsWorkspaceMember]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DocumentTemplateWriteSerializer
        return DocumentTemplateSerializer

    # ----- custom actions -----

    @action(detail=True, methods=["post"], url_path="blocks")
    def add_block(self, request, pk=None):
        """Add a block to this template at a given position (or append)."""
        template = self.get_object()
        serializer = DocumentTemplateBlockWriteSerializer(
            data=request.data,
            context={"template": template, **self.get_serializer_context()},
        )
        serializer.is_valid(raise_exception=True)

        # If no position provided, append after the last block
        if "position" not in request.data or request.data["position"] is None:
            last = (
                DocumentTemplateBlock.objects
                .filter(template=template)
                .order_by("-position")
                .first()
            )
            position = (last.position + 1) if last else 0
            serializer.validated_data["position"] = position

        serializer.save(template=template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="reorder")
    def reorder(self, request, pk=None):
        """Reorder template blocks by providing a list of {id, position}."""
        template = self.get_object()
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_items = serializer.validated_data["order"]
        block_ids = [item["id"] for item in order_items]

        with db_transaction.atomic():
            blocks = DocumentTemplateBlock.objects.filter(
                template=template, pk__in=block_ids
            )
            block_map = {b.pk: b for b in blocks}

            for item in order_items:
                block = block_map.get(item["id"])
                if block:
                    block.position = item["position"]

            DocumentTemplateBlock.objects.bulk_update(
                block_map.values(), ["position"]
            )

        return Response({"status": "reordered"})


# ===================================================================
# Template Blocks (CRUD)
# ===================================================================

class DocumentTemplateBlockViewSet(viewsets.ModelViewSet):
    """
    CRUD for template blocks.
    Scoped by workspace through the template relation.
    """

    queryset = DocumentTemplateBlock.objects.select_related("template", "block")
    #permission_classes = [IsWorkspaceMember]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DocumentTemplateBlockWriteSerializer
        return DocumentTemplateBlockSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ws_id = self.request.META.get("HTTP_X_WORKSPACE_ID")
        if ws_id:
            qs = qs.filter(template__workspace_id=ws_id)
        return qs

    def perform_create(self, serializer):
        template = serializer.validated_data.get("template")
        if not template:
            raise ValidationError({"template": "Template is required."})

        ws_id = get_workspace_id_from_request(self.request)
        if template.workspace_id != ws_id:
            raise ValidationError({"detail": "Template does not belong to workspace."})

        # Auto-append if position missing
        if serializer.validated_data.get("position") is None:
            last = (
                DocumentTemplateBlock.objects
                .filter(template=template)
                .order_by("-position")
                .first()
            )
            serializer.validated_data["position"] = (last.position + 1) if last else 0

        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        template = serializer.validated_data.get("template", instance.template)
        if template.pk != instance.template_id:
            raise ValidationError({"template": "Changing template is not allowed."})

        ws_id = get_workspace_id_from_request(self.request)
        if template.workspace_id != ws_id:
            raise ValidationError({"detail": "Template does not belong to workspace."})

        serializer.save()

    def perform_destroy(self, instance):
        ws_id = get_workspace_id_from_request(self.request)
        if instance.template.workspace_id != ws_id:
            raise ValidationError({"detail": "Template does not belong to workspace."})
        super().perform_destroy(instance)


# ===================================================================
# Document Instances
# ===================================================================

class DocumentViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """
    CRUD for documents.

    Extra actions:
    - POST   /documents/from-template/       — create from template
    - POST   /documents/{id}/render/          — render with Jinja2
    - POST   /documents/{id}/freeze/          — freeze document
    - PATCH  /documents/{id}/reorder-blocks/  — reorder document blocks
    """

    queryset = Document.objects.prefetch_related(
        "blocks", "category_assignments__category"
    ).select_related("status", "type", "template")
    #permission_classes = [IsWorkspaceMember]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DocumentWriteSerializer
        return DocumentSerializer

    # ----- custom actions -----

    @action(detail=False, methods=["post"], url_path="from-template")
    def from_template(self, request):
        """Create a document by copying blocks from a template."""
        serializer = CreateDocumentFromTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace_id = self.get_workspace_id()
        document = create_document_from_template(
            workspace_id=workspace_id,
            **serializer.validated_data,
        )

        out_serializer = DocumentSerializer(
            document, context=self.get_serializer_context()
        )
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="render")
    def render(self, request, pk=None):
        """Render the document using Jinja2 and its context snapshot."""
        document = self.get_object()
        serializer = RenderDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rendered_html = render_document(
            document=document,
            context_override=serializer.validated_data.get("context_override"),
        )
        return Response(
            {
                "rendered_html": rendered_html,
                "render_hash": document.render_hash,
            }
        )

    @action(detail=True, methods=["post"], url_path="freeze")
    def freeze(self, request, pk=None):
        """Freeze the document, making it immutable."""
        document = self.get_object()

        if document.frozen_at is not None:
            return Response(
                {"detail": "Document is already frozen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = freeze_document(document=document)
        out_serializer = DocumentSerializer(
            document, context=self.get_serializer_context()
        )
        return Response(out_serializer.data)

    @action(detail=True, methods=["patch"], url_path="reorder-blocks")
    def reorder_blocks(self, request, pk=None):
        """Reorder document blocks by providing a list of {id, position}."""
        document = self.get_object()

        if not document.is_editable:
            return Response(
                {"detail": "Document is not editable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_items = serializer.validated_data["order"]
        block_ids = [item["id"] for item in order_items]

        with db_transaction.atomic():
            blocks = DocumentBlock.objects.filter(
                document=document, pk__in=block_ids
            )
            block_map = {b.pk: b for b in blocks}

            for item in order_items:
                block = block_map.get(item["id"])
                if block:
                    block.position = item["position"]

            DocumentBlock.objects.bulk_update(block_map.values(), ["position"])

        return Response({"status": "reordered"})


# ===================================================================
# Document Blocks (CRUD)
# ===================================================================

class DocumentBlockViewSet(viewsets.ModelViewSet):
    """
    CRUD for document blocks.
    Scoped by workspace through the document relation.
    """

    queryset = DocumentBlock.objects.select_related("document")
    #permission_classes = [IsWorkspaceMember]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DocumentBlockWriteSerializer
        return DocumentBlockSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ws_id = self.request.META.get("HTTP_X_WORKSPACE_ID")
        if ws_id:
            qs = qs.filter(document__workspace_id=ws_id)
        return qs

    def _ensure_document_editable(self, document: Document):
        ws_id = get_workspace_id_from_request(self.request)
        if document.workspace_id != ws_id:
            raise ValidationError({"detail": "Document does not belong to workspace."})
        if not document.is_editable:
            raise ValidationError({"detail": "Document is not editable."})

    def perform_create(self, serializer):
        document = serializer.validated_data.get("document")
        if not document:
            raise ValidationError({"document": "Document is required."})
        self._ensure_document_editable(document)

        if serializer.validated_data.get("position") is None:
            last = (
                DocumentBlock.objects
                .filter(document=document)
                .order_by("-position")
                .first()
            )
            serializer.validated_data["position"] = (last.position + 1) if last else 0

        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        document = serializer.validated_data.get("document", instance.document)
        if document.pk != instance.document_id:
            raise ValidationError({"document": "Changing document is not allowed."})
        self._ensure_document_editable(document)
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_document_editable(instance.document)
        super().perform_destroy(instance)


# ===================================================================
# Signers
# ===================================================================

class PartyViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    """CRUD for signing parties."""

    queryset = Party.objects.all()
    serializer_class = PartySerializer
    #permission_classes = [IsWorkspaceMember]


class DocumentSignerViewSet(viewsets.ModelViewSet):
    """
    CRUD for document signers.

    The model does not have a direct workspace FK, so workspace filtering is
    done through the document relation.

    Extra actions:
    - POST /document-signers/{id}/events/  — create a signer audit event
    """

    queryset = DocumentSigner.objects.select_related(
        "party", "document"
    ).prefetch_related("events")
    #permission_classes = [IsWorkspaceMember]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DocumentSignerWriteSerializer
        return DocumentSignerSerializer

    def get_queryset(self):
        """Filter signers by workspace through document."""
        qs = super().get_queryset()
        ws_id = self.request.META.get("HTTP_X_WORKSPACE_ID")
        if ws_id:
            qs = qs.filter(document__workspace_id=ws_id)
        return qs

    # ----- custom actions -----

    @action(detail=True, methods=["post"], url_path="events")
    def create_event(self, request, pk=None):
        """Create an audit event for this signer."""
        signer = self.get_object()
        data = {**request.data, "document_signer": signer.pk}
        serializer = DocumentSignerEventSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
