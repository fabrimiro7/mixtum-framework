from django.db import models
from django.conf import settings
from django.utils import timezone


class MessageDirection(models.TextChoices):
    """Direction of the WhatsApp message."""
    INBOUND = "inbound", "Inbound (received)"
    OUTBOUND = "outbound", "Outbound (sent)"


class MessageStatus(models.TextChoices):
    """Status of the WhatsApp message."""
    QUEUED = "queued", "Queued"
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    READ = "read", "Read"
    FAILED = "failed", "Failed"
    RECEIVED = "received", "Received"


class WhatsAppConversation(models.Model):
    """
    Represents a WhatsApp conversation with a specific phone number.
    Groups messages by participant for easier conversation tracking.
    """
    # The phone number of the external participant (E.164 format, e.g., +393401234567)
    participant_phone = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Phone number in E.164 format (e.g., +393401234567)"
    )
    
    # The Twilio WhatsApp number used for this conversation
    twilio_phone = models.CharField(
        max_length=20,
        help_text="Twilio WhatsApp sender number (e.g., +14155238886)"
    )
    
    # Optional: link to a user in the system
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="whatsapp_conversations",
        help_text="Associated system user (if known)"
    )
    
    # Participant name (from WhatsApp profile or manually set)
    participant_name = models.CharField(max_length=255, blank=True, default="")
    
    # Conversation metadata
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    unread_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-last_message_at"]
        unique_together = ["participant_phone", "twilio_phone"]
        verbose_name = "WhatsApp Conversation"
        verbose_name_plural = "WhatsApp Conversations"
    
    def __str__(self):
        name = self.participant_name or self.participant_phone
        return f"Conversation with {name}"
    
    def mark_as_read(self):
        """Mark all unread messages in this conversation as read."""
        self.unread_count = 0
        self.save(update_fields=["unread_count", "updated_at"])


class WhatsAppMessage(models.Model):
    """
    Represents a single WhatsApp message, either inbound or outbound.
    """
    # Link to the conversation
    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    
    # Twilio identifiers
    twilio_sid = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Twilio Message SID"
    )
    
    # Message content
    body = models.TextField(blank=True, default="", help_text="Text content of the message")
    
    # Media attachments (URLs from Twilio)
    media_urls = models.JSONField(
        default=list,
        blank=True,
        help_text="List of media URLs attached to the message"
    )
    media_content_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of media content types"
    )
    
    # Message direction and status
    direction = models.CharField(
        max_length=10,
        choices=MessageDirection.choices,
        db_index=True
    )
    status = models.CharField(
        max_length=15,
        choices=MessageStatus.choices,
        default=MessageStatus.QUEUED
    )
    
    # Error handling
    error_code = models.CharField(max_length=10, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata from Twilio
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata from Twilio webhook"
    )
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "WhatsApp Message"
        verbose_name_plural = "WhatsApp Messages"
    
    def __str__(self):
        direction_label = "→" if self.direction == MessageDirection.OUTBOUND else "←"
        body_preview = (self.body[:50] + "...") if len(self.body) > 50 else self.body
        return f"{direction_label} {body_preview or '[media]'}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update conversation's last_message_at
        if is_new or "created_at" in (kwargs.get("update_fields") or []):
            self.conversation.last_message_at = self.created_at
            
            # Increment unread count for inbound messages
            if self.direction == MessageDirection.INBOUND:
                self.conversation.unread_count = models.F("unread_count") + 1
            
            self.conversation.save(update_fields=["last_message_at", "unread_count", "updated_at"])


class WhatsAppTemplate(models.Model):
    """
    Pre-approved WhatsApp message templates for sending notifications.
    Twilio/WhatsApp require pre-approved templates for business-initiated messages.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    # The template content (with placeholders like {{1}}, {{2}}, etc.)
    content_sid = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Twilio Content SID for approved template"
    )
    body_template = models.TextField(
        help_text="Template body with placeholders ({{1}}, {{2}}, etc.)"
    )
    
    # Template metadata
    language = models.CharField(max_length=10, default="it")
    category = models.CharField(
        max_length=50,
        default="utility",
        help_text="Template category (utility, marketing, authentication)"
    )
    
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
        verbose_name = "WhatsApp Template"
        verbose_name_plural = "WhatsApp Templates"
    
    def __str__(self):
        return self.name
    
    def render(self, variables: list) -> str:
        """
        Render the template with the given variables.
        Variables are substituted for {{1}}, {{2}}, etc.
        """
        result = self.body_template
        for i, var in enumerate(variables, start=1):
            result = result.replace(f"{{{{{i}}}}}", str(var))
        return result
