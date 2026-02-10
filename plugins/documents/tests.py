"""
Smoke tests for the documents plugin.

Covers the full document lifecycle:
1. Create taxonomy objects (type, category, status)
2. Create a block and a template with blocks
3. Create a document from the template
4. Render the document with context variables
5. Add a signer, freeze the document, and verify snapshots
"""

from django.test import TestCase
from rest_framework.test import APIClient

from base_modules.workspace.models import Workspace

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
from .services import (
    create_document_from_template,
    freeze_document,
    render_document,
)


class DocumentLifecycleTest(TestCase):
    """End-to-end test of the document creation → render → freeze lifecycle."""

    def setUp(self):
        self.workspace = Workspace.objects.create(
            workspace_name="Test Workspace",
        )

        # Taxonomy
        self.status_draft = DocumentStatus.objects.create(
            workspace=self.workspace,
            code="draft",
            title="Draft",
            is_terminal=False,
        )
        self.status_signed = DocumentStatus.objects.create(
            workspace=self.workspace,
            code="signed",
            title="Signed",
            is_terminal=True,
        )
        self.doc_type = DocumentType.objects.create(
            workspace=self.workspace,
            code="contract",
            title="Contract",
            requires_signature=True,
        )
        self.category = DocumentCategory.objects.create(
            workspace=self.workspace,
            slug="legal",
            title="Legal",
        )

        # Template + blocks
        self.template = DocumentTemplate.objects.create(
            workspace=self.workspace,
            title="Standard Contract",
        )
        self.block_header = Block.objects.create(
            workspace=self.workspace,
            title="Header",
            content="Contract for {{ client.first_name }} {{ client.last_name }}",
        )
        self.block_body = Block.objects.create(
            workspace=self.workspace,
            title="Body",
            content="Company: {{ company.name }}. Date: {{ meta.date | dateformat('%d/%m/%Y') }}",
        )
        DocumentTemplateBlock.objects.create(
            template=self.template,
            block=self.block_header,
            position=0,
        )
        DocumentTemplateBlock.objects.create(
            template=self.template,
            block=self.block_body,
            position=1,
        )

    # -----------------------------------------------------------------
    # Model tests
    # -----------------------------------------------------------------

    def test_template_blocks_snapshot_auto_populated(self):
        """Template blocks should auto-populate snapshots from source block."""
        tb = DocumentTemplateBlock.objects.filter(template=self.template).first()
        self.assertEqual(tb.title_snapshot, tb.block.title)
        self.assertEqual(tb.content_snapshot, tb.block.content)

    def test_document_type_unique_code(self):
        """Duplicate type code within same workspace should fail."""
        with self.assertRaises(Exception):
            DocumentType.objects.create(
                workspace=self.workspace,
                code="contract",  # duplicate
                title="Duplicate",
            )

    # -----------------------------------------------------------------
    # Service: create_document_from_template
    # -----------------------------------------------------------------

    def test_create_document_from_template(self):
        """Creating a document from a template copies blocks correctly."""
        doc = create_document_from_template(
            workspace_id=self.workspace.pk,
            title="My Contract",
            type_id=self.doc_type.pk,
            template_id=self.template.pk,
            status_code="draft",
            context={"client": {"first_name": "Mario", "last_name": "Rossi"}},
            category_ids=[self.category.pk],
        )
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.title, "My Contract")
        self.assertEqual(doc.status, self.status_draft)
        self.assertEqual(doc.type, self.doc_type)
        self.assertEqual(doc.template, self.template)

        # Check blocks were copied
        doc_blocks = DocumentBlock.objects.filter(document=doc).order_by("position")
        self.assertEqual(doc_blocks.count(), 2)
        self.assertEqual(doc_blocks[0].title, "Header")
        self.assertEqual(doc_blocks[1].title, "Body")

        # Check category assignment
        assignments = DocumentCategoryAssignment.objects.filter(document=doc)
        self.assertEqual(assignments.count(), 1)
        self.assertTrue(assignments.first().is_primary)

    # -----------------------------------------------------------------
    # Service: render_document
    # -----------------------------------------------------------------

    def test_render_document_with_context(self):
        """Rendering should interpolate Jinja2 placeholders."""
        doc = create_document_from_template(
            workspace_id=self.workspace.pk,
            title="Render Test",
            type_id=self.doc_type.pk,
            template_id=self.template.pk,
            context={
                "client": {"first_name": "Mario", "last_name": "Rossi"},
                "company": {"name": "Acme Srl"},
                "meta": {"date": "2026-02-10"},
            },
        )

        html = render_document(document=doc)

        self.assertIn("Mario", html)
        self.assertIn("Rossi", html)
        self.assertIn("Acme Srl", html)
        self.assertIn("10/02/2026", html)
        self.assertIsNotNone(doc.rendered_html)
        self.assertIsNotNone(doc.render_hash)
        self.assertEqual(len(doc.render_hash), 64)  # SHA-256 hex length

    def test_render_document_with_context_override(self):
        """Context override should merge with snapshot (override wins)."""
        doc = create_document_from_template(
            workspace_id=self.workspace.pk,
            title="Override Test",
            type_id=self.doc_type.pk,
            template_id=self.template.pk,
            context={
                "client": {"first_name": "Mario", "last_name": "Rossi"},
                "company": {"name": "Original"},
                "meta": {"date": "2026-01-01"},
            },
        )

        html = render_document(
            document=doc,
            context_override={
                "company": {"name": "Overridden Srl"},
            },
        )

        self.assertIn("Overridden Srl", html)
        # Client should still come from snapshot
        self.assertIn("Mario", html)

    # -----------------------------------------------------------------
    # Service: freeze_document
    # -----------------------------------------------------------------

    def test_freeze_document(self):
        """Freezing should set frozen_at and snapshot signers."""
        doc = create_document_from_template(
            workspace_id=self.workspace.pk,
            title="Freeze Test",
            type_id=self.doc_type.pk,
            template_id=self.template.pk,
            context={
                "client": {"first_name": "Luca", "last_name": "Bianchi"},
                "company": {"name": "Test Srl"},
                "meta": {"date": "2026-02-10"},
            },
        )

        # Add a signer
        party = Party.objects.create(
            workspace=self.workspace,
            first_name="Luca",
            last_name="Bianchi",
            email="luca@example.com",
        )
        signer = DocumentSigner.objects.create(
            document=doc,
            party=party,
            role="client",
            position=0,
        )

        # Freeze
        doc = freeze_document(document=doc)

        self.assertIsNotNone(doc.frozen_at)
        self.assertIsInstance(doc.signers_snapshot, list)
        self.assertEqual(len(doc.signers_snapshot), 1)
        self.assertEqual(doc.signers_snapshot[0]["role"], "client")
        self.assertEqual(doc.signers_snapshot[0]["party_email"], "luca@example.com")
        # Rendered HTML should be set after freeze
        self.assertIsNotNone(doc.rendered_html)

    def test_frozen_document_ignores_context_override(self):
        """After freezing, render should use snapshot only (no overrides)."""
        doc = create_document_from_template(
            workspace_id=self.workspace.pk,
            title="Frozen Override Test",
            type_id=self.doc_type.pk,
            template_id=self.template.pk,
            context={
                "client": {"first_name": "Anna", "last_name": "Verdi"},
                "company": {"name": "Frozen Corp"},
                "meta": {"date": "2026-06-01"},
            },
        )
        doc = freeze_document(document=doc)

        # Try to override after freeze — should be ignored
        html = render_document(
            document=doc,
            context_override={"company": {"name": "Should Not Appear"}},
        )

        self.assertIn("Frozen Corp", html)
        self.assertNotIn("Should Not Appear", html)

    # -----------------------------------------------------------------
    # Signer events
    # -----------------------------------------------------------------

    def test_signer_event_creation(self):
        """Creating a signer event should succeed and store payload."""
        doc = create_document_from_template(
            workspace_id=self.workspace.pk,
            title="Event Test",
            type_id=self.doc_type.pk,
            template_id=self.template.pk,
        )
        party = Party.objects.create(
            workspace=self.workspace,
            first_name="Test",
            last_name="Signer",
            email="signer@example.com",
        )
        signer = DocumentSigner.objects.create(
            document=doc,
            party=party,
            role="provider",
            position=0,
        )

        event = DocumentSignerEvent.objects.create(
            document_signer=signer,
            event_type="INVITED",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            payload={"channel": "email"},
        )

        self.assertEqual(event.event_type, "INVITED")
        self.assertEqual(event.payload["channel"], "email")
        self.assertEqual(signer.events.count(), 1)


class DocumentAPITest(TestCase):
    """
    Basic API smoke tests using DRF's APIClient.
    These verify that endpoints respond correctly with the X-Workspace-Id header.
    """

    def setUp(self):
        self.client = APIClient()
        self.workspace = Workspace.objects.create(
            workspace_name="API Test WS",
        )
        self.headers = {"HTTP_X_WORKSPACE_ID": str(self.workspace.pk)}

    def test_missing_workspace_header_returns_403(self):
        """Requests without X-Workspace-Id should be rejected."""
        response = self.client.get("/api/documents/types/")
        self.assertEqual(response.status_code, 403)

    def test_list_document_types(self):
        """GET /api/documents/types/ should return 200 with workspace header."""
        DocumentType.objects.create(
            workspace=self.workspace,
            code="quote",
            title="Quote",
        )
        response = self.client.get("/api/documents/types/", **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "quote")

    def test_create_block_via_api(self):
        """POST /api/documents/blocks/ should create a block."""
        response = self.client.post(
            "/api/documents/blocks/",
            data={
                "title": "Intro Block",
                "content": "Hello {{ client.first_name }}!",
                "is_active": True,
            },
            format="json",
            **self.headers,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Intro Block")
        self.assertEqual(Block.objects.count(), 1)

    def test_create_document_from_template_api(self):
        """POST /api/documents/documents/from-template/ should create a document."""
        status_obj = DocumentStatus.objects.create(
            workspace=self.workspace, code="draft", title="Draft"
        )
        doc_type = DocumentType.objects.create(
            workspace=self.workspace, code="contract", title="Contract"
        )
        template = DocumentTemplate.objects.create(
            workspace=self.workspace, title="Tpl"
        )
        block = Block.objects.create(
            workspace=self.workspace,
            title="B1",
            content="Hi {{ client.first_name }}",
        )
        DocumentTemplateBlock.objects.create(
            template=template, block=block, position=0
        )

        response = self.client.post(
            "/api/documents/documents/from-template/",
            data={
                "title": "API Contract",
                "type_id": doc_type.pk,
                "template_id": template.pk,
                "status_code": "draft",
                "context": {"client": {"first_name": "Test"}},
            },
            format="json",
            **self.headers,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "API Contract")
        self.assertEqual(len(response.data["blocks"]), 1)
