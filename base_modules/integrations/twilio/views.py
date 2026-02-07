from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import (
    WhatsAppMessage,
    WhatsAppConversation,
    WhatsAppTemplate,
)
from .serializers import (
    WhatsAppMessageSerializer,
    WhatsAppConversationSerializer,
    WhatsAppConversationDetailSerializer,
    WhatsAppTemplateSerializer,
    SendMessageSerializer,
    SendTemplateMessageSerializer,
)
from .services import (
    send_whatsapp_message,
    send_template_message,
    sync_message_status,
    get_conversation_messages,
)


class WhatsAppConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WhatsApp conversations.
    
    Provides CRUD operations and additional actions:
    - list: List all conversations
    - retrieve: Get conversation details with recent messages
    - messages: Get paginated messages for a conversation
    - send: Send a message in this conversation
    - mark_as_read: Mark all messages in conversation as read
    """
    queryset = WhatsAppConversation.objects.all()
    serializer_class = WhatsAppConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return WhatsAppConversationDetailSerializer
        return WhatsAppConversationSerializer
    
    def get_queryset(self):
        """
        Optionally filter conversations by:
        - user: conversations linked to a specific user
        - participant_phone: search by phone number
        - is_active: filter by active status
        - has_unread: filter conversations with unread messages
        """
        queryset = super().get_queryset()
        
        # Filter by user (if requesting own conversations)
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Search by participant phone
        phone = self.request.query_params.get("participant_phone")
        if phone:
            queryset = queryset.filter(participant_phone__icontains=phone)
        
        # Search by participant name
        name = self.request.query_params.get("participant_name")
        if name:
            queryset = queryset.filter(participant_name__icontains=name)
        
        # Filter active/inactive
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        
        # Filter by unread
        has_unread = self.request.query_params.get("has_unread")
        if has_unread is not None and has_unread.lower() == "true":
            queryset = queryset.filter(unread_count__gt=0)
        
        return queryset
    
    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """
        Get paginated messages for a conversation.
        
        Query params:
        - limit: Number of messages to return (default 50)
        - offset: Offset for pagination (default 0)
        - mark_as_read: Whether to mark messages as read (default false)
        """
        conversation = self.get_object()
        
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        mark_as_read = request.query_params.get("mark_as_read", "false").lower() == "true"
        
        messages = get_conversation_messages(
            conversation=conversation,
            limit=limit,
            offset=offset,
            mark_as_read=mark_as_read,
        )
        
        serializer = WhatsAppMessageSerializer(messages, many=True)
        return Response({
            "count": conversation.messages.count(),
            "limit": limit,
            "offset": offset,
            "results": serializer.data,
        })
    
    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        Send a message in this conversation.
        """
        conversation = self.get_object()
        
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = send_whatsapp_message(
            to_phone=conversation.participant_phone,
            body=serializer.validated_data["body"],
            media_urls=serializer.validated_data.get("media_urls"),
        )
        
        if result.success:
            return Response(
                WhatsAppMessageSerializer(result.message).data,
                status=status.HTTP_201_CREATED,
            )
        
        return Response(
            {
                "detail": "Failed to send message",
                "error_code": result.error_code,
                "error_message": result.error_message,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """
        Mark all messages in this conversation as read.
        """
        conversation = self.get_object()
        conversation.mark_as_read()
        
        return Response(
            WhatsAppConversationSerializer(conversation).data,
            status=status.HTTP_200_OK,
        )


class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WhatsApp messages.
    
    Provides CRUD operations and additional actions:
    - send: Send a new message
    - send_template: Send a template-based message
    - sync_status: Sync message status from Twilio
    """
    queryset = WhatsAppMessage.objects.select_related("conversation").all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally filter messages by:
        - conversation: filter by conversation ID
        - direction: filter by direction (inbound/outbound)
        - status: filter by status
        """
        queryset = super().get_queryset()
        
        conversation_id = self.request.query_params.get("conversation")
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        direction = self.request.query_params.get("direction")
        if direction:
            queryset = queryset.filter(direction=direction)
        
        msg_status = self.request.query_params.get("status")
        if msg_status:
            queryset = queryset.filter(status=msg_status)
        
        return queryset
    
    @action(detail=False, methods=["post"])
    def send(self, request):
        """
        Send a new WhatsApp message.
        
        Request body:
        - to_phone: Recipient phone number
        - body: Message text
        - media_urls: Optional list of media URLs
        """
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = send_whatsapp_message(
            to_phone=serializer.validated_data["to_phone"],
            body=serializer.validated_data["body"],
            media_urls=serializer.validated_data.get("media_urls"),
        )
        
        if result.success:
            return Response(
                WhatsAppMessageSerializer(result.message).data,
                status=status.HTTP_201_CREATED,
            )
        
        return Response(
            {
                "detail": "Failed to send message",
                "error_code": result.error_code,
                "error_message": result.error_message,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    @action(detail=False, methods=["post"])
    def send_template(self, request):
        """
        Send a template-based WhatsApp message.
        
        Request body:
        - to_phone: Recipient phone number
        - template_slug: Template slug identifier
        - variables: List of template variables
        """
        serializer = SendTemplateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = send_template_message(
            to_phone=serializer.validated_data["to_phone"],
            template=serializer.validated_data["template_slug"],
            variables=serializer.validated_data.get("variables", []),
        )
        
        if result.success:
            return Response(
                WhatsAppMessageSerializer(result.message).data,
                status=status.HTTP_201_CREATED,
            )
        
        return Response(
            {
                "detail": "Failed to send template message",
                "error_code": result.error_code,
                "error_message": result.error_message,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    @action(detail=True, methods=["post"])
    def sync_status(self, request, pk=None):
        """
        Sync message status from Twilio API.
        """
        message = self.get_object()
        
        if not message.twilio_sid:
            return Response(
                {"detail": "Message has no Twilio SID"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        updated_message = sync_message_status(message)
        
        return Response(
            WhatsAppMessageSerializer(updated_message).data,
            status=status.HTTP_200_OK,
        )


class WhatsAppTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WhatsApp message templates.
    
    Provides CRUD operations for managing pre-approved message templates.
    """
    queryset = WhatsAppTemplate.objects.all()
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter templates by category or active status."""
        queryset = super().get_queryset()
        
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        
        return queryset
    
    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        """
        Preview a template with sample variables.
        
        Request body:
        - variables: List of sample variables
        """
        template = self.get_object()
        variables = request.data.get("variables", [])
        
        rendered = template.render(variables)
        
        return Response({
            "template": WhatsAppTemplateSerializer(template).data,
            "rendered": rendered,
        })
