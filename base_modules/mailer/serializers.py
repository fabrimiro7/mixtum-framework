from rest_framework import serializers
from .models import Email, EmailTemplate, EmailAttachment, EmailStatus

class EmailAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAttachment
        fields = ["id", "name", "mimetype", "size", "file", "created_at"]
        read_only_fields = ["id", "size", "created_at"]

class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            "id", "name", "slug",
            "subject_template", "html_template", "text_template",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class EmailSerializer(serializers.ModelSerializer):
    attachments = EmailAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Email
        fields = [
            "id",
            "from_email", "to", "cc", "bcc",
            "subject", "body_text", "body_html",
            "template", "context",
            "status", "priority",
            "scheduled_at", "sent_at", "retries", "last_error",
            "created_at", "updated_at",
            "attachments",
        ]
        read_only_fields = ["status", "sent_at", "retries", "last_error", "created_at", "updated_at"]

class EmailSendSerializer(serializers.Serializer):
    """
    Serializer per l'azione custom 'send' su un'Email esistente.
    """
    context_override = serializers.DictField(required=False, default=dict)
    fail_silently = serializers.BooleanField(required=False, default=False)
