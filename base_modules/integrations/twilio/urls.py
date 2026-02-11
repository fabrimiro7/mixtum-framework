from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WhatsAppConversationViewSet,
    WhatsAppMessageViewSet,
    WhatsAppTemplateViewSet,
)
from .webhooks import whatsapp_incoming, whatsapp_status


# REST API router
router = DefaultRouter()
router.register(
    r"conversations", 
    WhatsAppConversationViewSet, 
    basename="whatsapp-conversation"
)
router.register(
    r"messages", 
    WhatsAppMessageViewSet, 
    basename="whatsapp-message"
)
router.register(
    r"templates", 
    WhatsAppTemplateViewSet, 
    basename="whatsapp-template"
)

urlpatterns = [
    # REST API endpoints
    path("", include(router.urls)),
    
    # Twilio webhooks (for receiving messages and status updates)
    path("webhooks/incoming/", whatsapp_incoming, name="whatsapp-webhook-incoming"),
    path("webhooks/status/", whatsapp_status, name="whatsapp-webhook-status"),
]
