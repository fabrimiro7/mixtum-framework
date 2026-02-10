"""
DRF serializers for the documents plugin.

Conventions:
- Read serializers include nested children (blocks, signers) as read-only.
- Write / create / update serializers accept PK references for FK fields.
- Separate lightweight serializers are provided for list endpoints vs. detail.
"""

from rest_framework import serializers

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
# Core Taxonomy
# ===================================================================

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = [
            "id",
            "workspace",
            "code",
            "title",
            "description",
            "default_template",
            "requires_signature",
            "is_active",
            "sort_order",
        ]
        read_only_fields = ["id", "workspace"]


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = [
            "id",
            "workspace",
            "slug",
            "title",
            "parent",
            "color",
            "is_active",
            "sort_order",
        ]
        read_only_fields = ["id", "workspace"]


class DocumentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentStatus
        fields = [
            "id",
            "workspace",
            "code",
            "title",
            "is_terminal",
            "sort_order",
        ]
        read_only_fields = ["id", "workspace"]


# ===================================================================
# Blocks & Templates
# ===================================================================

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = [
            "id",
            "workspace",
            "title",
            "content",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]


class DocumentTemplateBlockSerializer(serializers.ModelSerializer):
    """Read serializer — nested inside DocumentTemplateSerializer."""

    block_title = serializers.CharField(source="block.title", read_only=True)

    class Meta:
        model = DocumentTemplateBlock
        fields = [
            "id",
            "block",
            "block_title",
            "title_snapshot",
            "content_snapshot",
            "position",
        ]
        read_only_fields = ["id"]


class DocumentTemplateBlockWriteSerializer(serializers.ModelSerializer):
    """Write serializer for adding / updating a template block."""

    class Meta:
        model = DocumentTemplateBlock
        fields = [
            "id",
            "block",
            "title_snapshot",
            "content_snapshot",
            "position",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """
        If snapshots are not provided, they will be auto-populated by the model's
        save() method.  Validate position uniqueness within the template.
        """
        template = self.context.get("template")
        position = attrs.get("position")
        if template and position is not None:
            qs = DocumentTemplateBlock.objects.filter(
                template=template,
                position=position,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"position": "A block already exists at this position in the template."}
                )
        return attrs


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Read serializer — includes nested template blocks."""

    template_blocks = DocumentTemplateBlockSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentTemplate
        fields = [
            "id",
            "workspace",
            "title",
            "description",
            "template_blocks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]


class DocumentTemplateWriteSerializer(serializers.ModelSerializer):
    """Write serializer — no nested blocks (those are managed via separate endpoints)."""

    class Meta:
        model = DocumentTemplate
        fields = [
            "id",
            "workspace",
            "title",
            "description",
        ]
        read_only_fields = ["id", "workspace"]


class ReorderSerializer(serializers.Serializer):
    """
    Generic reorder payload.
    Expects a list of objects with ``id`` and ``position``.
    """

    order = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of {"id": <int>, "position": <int>} items.',
    )

    def validate_order(self, value):
        positions = []
        for item in value:
            if "id" not in item or "position" not in item:
                raise serializers.ValidationError(
                    'Each item must have "id" and "position" keys.'
                )
            try:
                item["id"] = int(item["id"])
                item["position"] = int(item["position"])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    '"id" and "position" must be integers.'
                )
            if item["position"] in positions:
                raise serializers.ValidationError(
                    f"Duplicate position {item['position']}."
                )
            positions.append(item["position"])
        return value


# ===================================================================
# Document Instances
# ===================================================================

class DocumentBlockSerializer(serializers.ModelSerializer):
    """Read serializer — nested inside DocumentSerializer."""

    class Meta:
        model = DocumentBlock
        fields = [
            "id",
            "source_template_block",
            "title",
            "content",
            "position",
        ]
        read_only_fields = ["id"]


class DocumentCategoryAssignmentSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(source="category.title", read_only=True)

    class Meta:
        model = DocumentCategoryAssignment
        fields = ["id", "category", "category_title", "is_primary"]
        read_only_fields = ["id"]


class DocumentSerializer(serializers.ModelSerializer):
    """Read serializer — includes nested blocks and category assignments."""

    blocks = DocumentBlockSerializer(many=True, read_only=True)
    category_assignments = DocumentCategoryAssignmentSerializer(
        many=True, read_only=True
    )
    is_editable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "workspace",
            "title",
            "status",
            "type",
            "template",
            "categories",
            "category_assignments",
            "context_snapshot",
            "signers_snapshot",
            "rendered_html",
            "render_hash",
            "frozen_at",
            "is_editable",
            "blocks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "rendered_html",
            "render_hash",
            "frozen_at",
            "signers_snapshot",
            "created_at",
            "updated_at",
        ]


class DocumentWriteSerializer(serializers.ModelSerializer):
    """Write serializer — accepts FK ids, no nested blocks."""

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "status",
            "type",
            "template",
            "context_snapshot",
        ]
        read_only_fields = ["id"]


class CreateDocumentFromTemplateSerializer(serializers.Serializer):
    """Payload for the ``from-template`` action."""

    title = serializers.CharField(max_length=255)
    type_id = serializers.IntegerField()
    template_id = serializers.IntegerField()
    status_code = serializers.SlugField(default="draft")
    context = serializers.JSONField(required=False, default=dict)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )


class RenderDocumentSerializer(serializers.Serializer):
    """Optional context override for the render action."""

    context_override = serializers.JSONField(required=False, default=None)


# ===================================================================
# Signers
# ===================================================================

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = [
            "id",
            "workspace",
            "user_id",
            "first_name",
            "last_name",
            "company_name",
            "email",
            "phone",
            "tax_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]


class DocumentSignerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSignerEvent
        fields = [
            "id",
            "document_signer",
            "event_type",
            "ip_address",
            "user_agent",
            "payload",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DocumentSignerSerializer(serializers.ModelSerializer):
    events = DocumentSignerEventSerializer(many=True, read_only=True)
    party_name = serializers.SerializerMethodField()

    class Meta:
        model = DocumentSigner
        fields = [
            "id",
            "document",
            "party",
            "party_name",
            "role",
            "position",
            "routing_mode",
            "status",
            "invited_at",
            "viewed_at",
            "signed_at",
            "rejected_at",
            "signature_method",
            "provider_envelope_id",
            "provider_signer_id",
            "events",
        ]
        read_only_fields = [
            "id",
            "invited_at",
            "viewed_at",
            "signed_at",
            "rejected_at",
        ]

    def get_party_name(self, obj) -> str:
        return str(obj.party)

    def validate(self, attrs):
        """
        Enforce sequential-mode position uniqueness at the serializer level
        (model-level clean() also checks, but we want nice API error messages).
        """
        document = attrs.get("document", getattr(self.instance, "document", None))
        routing_mode = attrs.get(
            "routing_mode",
            getattr(self.instance, "routing_mode", "parallel"),
        )
        position = attrs.get(
            "position", getattr(self.instance, "position", 0)
        )

        if routing_mode == "sequential" and document:
            qs = DocumentSigner.objects.filter(
                document=document,
                position=position,
                routing_mode="sequential",
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {
                        "position": (
                            "Sequential signers must have unique positions "
                            "within the same document."
                        )
                    }
                )
        return attrs


class DocumentSignerWriteSerializer(serializers.ModelSerializer):
    """Write serializer — no nested events."""

    class Meta:
        model = DocumentSigner
        fields = [
            "id",
            "document",
            "party",
            "role",
            "position",
            "routing_mode",
            "status",
            "signature_method",
            "provider_envelope_id",
            "provider_signer_id",
        ]
        read_only_fields = ["id"]
