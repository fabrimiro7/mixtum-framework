"""
Tests for Twilio WhatsApp Integration
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from .models import (
    WhatsAppConversation,
    WhatsAppMessage,
    WhatsAppTemplate,
    MessageDirection,
    MessageStatus,
)
from .services import (
    format_whatsapp_number,
    extract_phone_number,
    get_or_create_conversation,
    SendMessageResult,
)


User = get_user_model()


class WhatsAppNumberFormattingTests(TestCase):
    """Tests for phone number formatting utilities."""
    
    def test_format_whatsapp_number_already_formatted(self):
        """Test that already formatted numbers are not changed."""
        result = format_whatsapp_number("whatsapp:+393401234567")
        self.assertEqual(result, "whatsapp:+393401234567")
    
    def test_format_whatsapp_number_with_plus(self):
        """Test formatting a number with + prefix."""
        result = format_whatsapp_number("+393401234567")
        self.assertEqual(result, "whatsapp:+393401234567")
    
    def test_format_whatsapp_number_without_plus(self):
        """Test formatting a number without + prefix."""
        result = format_whatsapp_number("393401234567")
        self.assertEqual(result, "whatsapp:+393401234567")
    
    def test_extract_phone_number_with_prefix(self):
        """Test extracting phone from whatsapp: prefix."""
        result = extract_phone_number("whatsapp:+393401234567")
        self.assertEqual(result, "+393401234567")
    
    def test_extract_phone_number_without_prefix(self):
        """Test extracting phone without prefix."""
        result = extract_phone_number("+393401234567")
        self.assertEqual(result, "+393401234567")


class WhatsAppConversationTests(TestCase):
    """Tests for WhatsAppConversation model."""
    
    def test_create_conversation(self):
        """Test creating a conversation."""
        conversation = WhatsAppConversation.objects.create(
            participant_phone="+393401234567",
            twilio_phone="+14155238886",
            participant_name="Test User",
        )
        self.assertEqual(conversation.participant_phone, "+393401234567")
        self.assertEqual(conversation.twilio_phone, "+14155238886")
        self.assertEqual(conversation.participant_name, "Test User")
        self.assertTrue(conversation.is_active)
        self.assertEqual(conversation.unread_count, 0)
    
    def test_get_or_create_conversation(self):
        """Test get_or_create_conversation service function."""
        # First call should create
        conv1 = get_or_create_conversation(
            participant_phone="+393401234567",
            twilio_phone="+14155238886",
        )
        self.assertIsNotNone(conv1.id)
        
        # Second call should return existing
        conv2 = get_or_create_conversation(
            participant_phone="+393401234567",
            twilio_phone="+14155238886",
        )
        self.assertEqual(conv1.id, conv2.id)
    
    def test_mark_as_read(self):
        """Test marking conversation as read."""
        conversation = WhatsAppConversation.objects.create(
            participant_phone="+393401234567",
            twilio_phone="+14155238886",
            unread_count=5,
        )
        conversation.mark_as_read()
        conversation.refresh_from_db()
        self.assertEqual(conversation.unread_count, 0)


class WhatsAppMessageTests(TestCase):
    """Tests for WhatsAppMessage model."""
    
    def setUp(self):
        self.conversation = WhatsAppConversation.objects.create(
            participant_phone="+393401234567",
            twilio_phone="+14155238886",
        )
    
    def test_create_message(self):
        """Test creating a message."""
        message = WhatsAppMessage.objects.create(
            conversation=self.conversation,
            body="Hello, World!",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
        )
        self.assertEqual(message.body, "Hello, World!")
        self.assertEqual(message.direction, MessageDirection.OUTBOUND)
        self.assertEqual(message.status, MessageStatus.SENT)
    
    def test_message_updates_conversation(self):
        """Test that creating a message updates conversation last_message_at."""
        initial_last = self.conversation.last_message_at
        
        WhatsAppMessage.objects.create(
            conversation=self.conversation,
            body="Test message",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
        )
        
        self.conversation.refresh_from_db()
        self.assertIsNotNone(self.conversation.last_message_at)
    
    def test_inbound_message_increments_unread(self):
        """Test that inbound messages increment unread count."""
        initial_count = self.conversation.unread_count
        
        WhatsAppMessage.objects.create(
            conversation=self.conversation,
            body="Incoming message",
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
        )
        
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.unread_count, initial_count + 1)


class WhatsAppTemplateTests(TestCase):
    """Tests for WhatsAppTemplate model."""
    
    def test_create_template(self):
        """Test creating a template."""
        template = WhatsAppTemplate.objects.create(
            name="Reminder Template",
            slug="reminder-template",
            body_template="Ciao {{1}}, ricorda il tuo appuntamento alle {{2}}.",
        )
        self.assertEqual(template.name, "Reminder Template")
        self.assertTrue(template.is_active)
    
    def test_template_render(self):
        """Test template rendering with variables."""
        template = WhatsAppTemplate.objects.create(
            name="Test Template",
            slug="test-template",
            body_template="Ciao {{1}}, il tuo codice è {{2}}.",
        )
        
        rendered = template.render(["Mario", "123456"])
        self.assertEqual(rendered, "Ciao Mario, il tuo codice è 123456.")
    
    def test_template_render_partial(self):
        """Test template rendering with fewer variables."""
        template = WhatsAppTemplate.objects.create(
            name="Test Template",
            slug="test-template-2",
            body_template="Ciao {{1}}, il tuo codice è {{2}}.",
        )
        
        rendered = template.render(["Mario"])
        self.assertEqual(rendered, "Ciao Mario, il tuo codice è {{2}}.")


class SendMessageResultTests(TestCase):
    """Tests for SendMessageResult dataclass."""
    
    def test_success_result(self):
        """Test creating a success result."""
        result = SendMessageResult(
            success=True,
            twilio_sid="SM1234567890",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.twilio_sid, "SM1234567890")
        self.assertIsNone(result.error_code)
    
    def test_failure_result(self):
        """Test creating a failure result."""
        result = SendMessageResult(
            success=False,
            error_code="21211",
            error_message="Invalid phone number",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "21211")
        self.assertEqual(result.error_message, "Invalid phone number")
