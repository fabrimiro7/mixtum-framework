from django.contrib import admin
from .models import WhatsAppConversation, WhatsAppMessage, WhatsAppTemplate


@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "participant_phone",
        "participant_name",
        "twilio_phone",
        "user",
        "is_active",
        "unread_count",
        "last_message_at",
        "created_at",
    ]
    list_filter = ["is_active", "created_at", "twilio_phone"]
    search_fields = ["participant_phone", "participant_name"]
    readonly_fields = ["created_at", "updated_at", "last_message_at"]
    raw_id_fields = ["user"]
    ordering = ["-last_message_at"]


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "twilio_sid",
        "get_participant",
        "direction",
        "status",
        "body_preview",
        "sent_at",
        "created_at",
    ]
    list_filter = ["direction", "status", "created_at"]
    search_fields = ["twilio_sid", "body", "conversation__participant_phone"]
    readonly_fields = [
        "twilio_sid",
        "created_at",
        "updated_at",
        "sent_at",
        "delivered_at",
        "read_at",
    ]
    raw_id_fields = ["conversation"]
    ordering = ["-created_at"]
    
    def get_participant(self, obj):
        return obj.conversation.participant_phone
    get_participant.short_description = "Participant"
    
    def body_preview(self, obj):
        if obj.body:
            return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body
        return "[media]"
    body_preview.short_description = "Message"


@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "slug",
        "category",
        "language",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "category", "language"]
    search_fields = ["name", "slug", "body_template"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]
