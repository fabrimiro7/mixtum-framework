from rest_framework import serializers
from .models import (
    WhatsAppMessage,
    WhatsAppConversation,
    WhatsAppTemplate,
    MessageDirection,
    MessageStatus,
)


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp messages."""
    
    direction_display = serializers.CharField(
        source="get_direction_display", 
        read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", 
        read_only=True
    )
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            "id",
            "conversation",
            "twilio_sid",
            "body",
            "media_urls",
            "media_content_types",
            "direction",
            "direction_display",
            "status",
            "status_display",
            "error_code",
            "error_message",
            "sent_at",
            "delivered_at",
            "read_at",
            "created_at",
            "updated_at",
            "metadata",
        ]
        read_only_fields = [
            "id",
            "twilio_sid",
            "direction",
            "status",
            "error_code",
            "error_message",
            "sent_at",
            "delivered_at",
            "read_at",
            "created_at",
            "updated_at",
        ]


class WhatsAppConversationSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp conversations."""
    
    last_message = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WhatsAppConversation
        fields = [
            "id",
            "participant_phone",
            "twilio_phone",
            "user",
            "participant_name",
            "is_active",
            "last_message_at",
            "unread_count",
            "created_at",
            "updated_at",
            "last_message",
            "messages_count",
        ]
        read_only_fields = [
            "id",
            "twilio_phone",
            "last_message_at",
            "unread_count",
            "created_at",
            "updated_at",
        ]
    
    def get_last_message(self, obj):
        """Get the last message in the conversation."""
        last = obj.messages.order_by("-created_at").first()
        if last:
            return {
                "id": last.id,
                "body": last.body[:100] if last.body else "",
                "direction": last.direction,
                "status": last.status,
                "created_at": last.created_at,
            }
        return None
    
    def get_messages_count(self, obj):
        """Get total message count in the conversation."""
        return obj.messages.count()


class WhatsAppConversationDetailSerializer(WhatsAppConversationSerializer):
    """Detailed serializer including recent messages."""
    
    recent_messages = serializers.SerializerMethodField()
    
    class Meta(WhatsAppConversationSerializer.Meta):
        fields = WhatsAppConversationSerializer.Meta.fields + ["recent_messages"]
    
    def get_recent_messages(self, obj):
        """Get the 20 most recent messages."""
        messages = obj.messages.order_by("-created_at")[:20]
        return WhatsAppMessageSerializer(messages, many=True).data


class WhatsAppTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp message templates."""
    
    class Meta:
        model = WhatsAppTemplate
        fields = [
            "id",
            "name",
            "slug",
            "content_sid",
            "body_template",
            "language",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# -----------------------------------------------------------------------------
# Action Serializers (for custom actions)
# -----------------------------------------------------------------------------
class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a new WhatsApp message."""
    
    to_phone = serializers.CharField(
        max_length=20,
        help_text="Recipient phone number in E.164 format (e.g., +393401234567)"
    )
    body = serializers.CharField(
        max_length=4096,
        help_text="Message text content"
    )
    media_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
        help_text="Optional list of media URLs to attach"
    )
    
    def validate_to_phone(self, value):
        """Validate phone number format."""
        value = value.strip()
        # Remove whatsapp: prefix if present for validation
        if value.startswith("whatsapp:"):
            value = value[9:]
        # Basic validation
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Phone number must start with + (E.164 format)"
            )
        if len(value) < 8 or len(value) > 16:
            raise serializers.ValidationError(
                "Phone number must be between 8 and 16 characters"
            )
        return value


class SendTemplateMessageSerializer(serializers.Serializer):
    """Serializer for sending a template-based message."""
    
    to_phone = serializers.CharField(
        max_length=20,
        help_text="Recipient phone number in E.164 format"
    )
    template_slug = serializers.SlugField(
        help_text="Template slug identifier"
    )
    variables = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
        help_text="List of variables to substitute in the template"
    )
    
    def validate_to_phone(self, value):
        """Validate phone number format."""
        value = value.strip()
        if value.startswith("whatsapp:"):
            value = value[9:]
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Phone number must start with + (E.164 format)"
            )
        return value
    
    def validate_template_slug(self, value):
        """Validate that the template exists."""
        if not WhatsAppTemplate.objects.filter(slug=value, is_active=True).exists():
            raise serializers.ValidationError(
                f"Template with slug '{value}' not found or is inactive"
            )
        return value


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking messages as read."""
    
    # No input needed for this action
    pass


class SyncStatusSerializer(serializers.Serializer):
    """Serializer for syncing message status from Twilio."""
    
    # No input needed for this action
    pass
