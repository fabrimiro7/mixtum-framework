from django.contrib import admin
from .models import *


class AttachmentAdmin(admin.ModelAdmin):
    """
    Admin custom for Conversation model
    """
    list_display = ("title", "author")
    search_fields = ("title", "author")
    
admin.site.register(Attachment)


