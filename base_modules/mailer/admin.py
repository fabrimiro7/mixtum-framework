from django.contrib import admin
from django.utils.html import format_html
from .models import EmailTemplate, Email, EmailAttachment, EmailStatus
from .services import send_email

class EmailAttachmentInline(admin.TabularInline):
    model = EmailAttachment
    extra = 0
    readonly_fields = ("size",)

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "updated_at")
    search_fields = ("name", "slug")

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "status", "created_at", "sent_at", "short_to")
    list_filter = ("status", "created_at", "sent_at")
    search_fields = ("subject", "last_error")
    inlines = [EmailAttachmentInline]
    readonly_fields = ("sent_at", "retries", "last_error", "created_at", "updated_at")

    actions = ["action_send_emails"]

    def short_to(self, obj):
        return ", ".join(obj.to[:3]) + ("..." if len(obj.to) > 3 else "")
    short_to.short_description = "To"

    def action_send_emails(self, request, queryset):
        sent, failed = 0, 0
        for email in queryset:
            try:
                send_email(email, fail_silently=True)
                email.refresh_from_db()
                if email.status == EmailStatus.SENT:
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        self.message_user(request, f"Inviate: {sent}, fallite: {failed}")
    action_send_emails.short_description = "Invia email selezionate"
