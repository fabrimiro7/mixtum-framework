"""
Twilio WhatsApp API Service Layer

Provides primitives for:
- Sending WhatsApp messages (text, media, templates)
- Reading message history
- Managing conversations
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from .models import (
    WhatsAppMessage,
    WhatsAppConversation,
    WhatsAppTemplate,
    MessageDirection,
    MessageStatus,
)


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
def get_twilio_config() -> Dict[str, str]:
    """
    Get Twilio configuration from Django settings.
    Expected settings:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_WHATSAPP_NUMBER (e.g., 'whatsapp:+14155238886')
    """
    return {
        "account_sid": getattr(settings, "TWILIO_ACCOUNT_SID", ""),
        "auth_token": getattr(settings, "TWILIO_AUTH_TOKEN", ""),
        "whatsapp_number": getattr(settings, "TWILIO_WHATSAPP_NUMBER", ""),
    }


def get_twilio_client() -> Client:
    """
    Create and return a Twilio REST API client.
    """
    config = get_twilio_config()
    if not config["account_sid"] or not config["auth_token"]:
        raise ValueError(
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be configured in settings."
        )
    return Client(config["account_sid"], config["auth_token"])


def format_whatsapp_number(phone: str) -> str:
    """
    Ensure phone number is in WhatsApp format: 'whatsapp:+1234567890'
    """
    phone = phone.strip()
    if phone.startswith("whatsapp:"):
        return phone
    # Ensure it starts with +
    if not phone.startswith("+"):
        phone = f"+{phone}"
    return f"whatsapp:{phone}"


def extract_phone_number(whatsapp_number: str) -> str:
    """
    Extract phone number from WhatsApp format.
    'whatsapp:+1234567890' -> '+1234567890'
    """
    if whatsapp_number.startswith("whatsapp:"):
        return whatsapp_number[9:]
    return whatsapp_number


# -----------------------------------------------------------------------------
# Data Classes for API responses
# -----------------------------------------------------------------------------
@dataclass
class SendMessageResult:
    """Result of a send message operation."""
    success: bool
    message: Optional[WhatsAppMessage] = None
    twilio_sid: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# -----------------------------------------------------------------------------
# Conversation Management
# -----------------------------------------------------------------------------
def get_or_create_conversation(
    participant_phone: str,
    twilio_phone: Optional[str] = None,
    participant_name: Optional[str] = None,
    user=None,
) -> WhatsAppConversation:
    """
    Get or create a conversation with the given participant.
    """
    if twilio_phone is None:
        config = get_twilio_config()
        twilio_phone = extract_phone_number(config["whatsapp_number"])
    
    participant_phone = extract_phone_number(participant_phone)
    twilio_phone = extract_phone_number(twilio_phone)
    
    conversation, created = WhatsAppConversation.objects.get_or_create(
        participant_phone=participant_phone,
        twilio_phone=twilio_phone,
        defaults={
            "participant_name": participant_name or "",
            "user": user,
        }
    )
    
    if not created and participant_name and not conversation.participant_name:
        conversation.participant_name = participant_name
        conversation.save(update_fields=["participant_name", "updated_at"])
    
    if not created and user and not conversation.user:
        conversation.user = user
        conversation.save(update_fields=["user", "updated_at"])
    
    return conversation


def get_conversation_messages(
    conversation: Union[int, WhatsAppConversation],
    limit: int = 50,
    offset: int = 0,
    mark_as_read: bool = False,
) -> List[WhatsAppMessage]:
    """
    Get messages from a conversation with pagination.
    """
    if isinstance(conversation, int):
        conversation = WhatsAppConversation.objects.get(pk=conversation)
    
    messages = list(
        conversation.messages.all()
        .order_by("-created_at")[offset : offset + limit]
    )
    
    if mark_as_read:
        conversation.mark_as_read()
    
    return messages


# -----------------------------------------------------------------------------
# Message Sending
# -----------------------------------------------------------------------------
def send_whatsapp_message(
    to_phone: str,
    body: str,
    media_urls: Optional[List[str]] = None,
    from_phone: Optional[str] = None,
    save_to_db: bool = True,
) -> SendMessageResult:
    """
    Send a WhatsApp message using Twilio API.
    
    Args:
        to_phone: Recipient phone number (E.164 format or whatsapp: prefix)
        body: Message text content
        media_urls: Optional list of media URLs to attach
        from_phone: Sender phone number (defaults to TWILIO_WHATSAPP_NUMBER)
        save_to_db: Whether to save the message to the database
    
    Returns:
        SendMessageResult with success status and message details
    """
    config = get_twilio_config()
    
    if from_phone is None:
        from_phone = config["whatsapp_number"]
    
    to_formatted = format_whatsapp_number(to_phone)
    from_formatted = format_whatsapp_number(from_phone)
    
    # Create conversation and message record first
    message_obj = None
    if save_to_db:
        conversation = get_or_create_conversation(
            participant_phone=to_phone,
            twilio_phone=from_phone,
        )
        message_obj = WhatsAppMessage.objects.create(
            conversation=conversation,
            body=body,
            media_urls=media_urls or [],
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.QUEUED,
        )
    
    try:
        client = get_twilio_client()
        
        # Build message parameters
        message_params = {
            "from_": from_formatted,
            "to": to_formatted,
            "body": body,
        }
        
        if media_urls:
            message_params["media_url"] = media_urls
        
        # Send via Twilio
        twilio_message = client.messages.create(**message_params)
        
        # Update message record with Twilio SID
        if message_obj:
            message_obj.twilio_sid = twilio_message.sid
            message_obj.status = MessageStatus.SENT
            message_obj.sent_at = timezone.now()
            message_obj.save(update_fields=[
                "twilio_sid", "status", "sent_at", "updated_at"
            ])
        
        logger.info(
            f"WhatsApp message sent successfully. SID: {twilio_message.sid}, "
            f"To: {to_phone}"
        )
        
        return SendMessageResult(
            success=True,
            message=message_obj,
            twilio_sid=twilio_message.sid,
        )
    
    except TwilioRestException as e:
        logger.error(
            f"Failed to send WhatsApp message. Error: {e.code} - {e.msg}"
        )
        
        if message_obj:
            message_obj.status = MessageStatus.FAILED
            message_obj.error_code = str(e.code)
            message_obj.error_message = e.msg
            message_obj.save(update_fields=[
                "status", "error_code", "error_message", "updated_at"
            ])
        
        return SendMessageResult(
            success=False,
            message=message_obj,
            error_code=str(e.code),
            error_message=e.msg,
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error sending WhatsApp message: {e}")
        
        if message_obj:
            message_obj.status = MessageStatus.FAILED
            message_obj.error_message = str(e)
            message_obj.save(update_fields=[
                "status", "error_message", "updated_at"
            ])
        
        return SendMessageResult(
            success=False,
            message=message_obj,
            error_message=str(e),
        )


def send_template_message(
    to_phone: str,
    template: Union[str, int, WhatsAppTemplate],
    variables: List[str],
    from_phone: Optional[str] = None,
    save_to_db: bool = True,
) -> SendMessageResult:
    """
    Send a WhatsApp template message (for business-initiated conversations).
    
    Args:
        to_phone: Recipient phone number
        template: Template object, ID, or slug
        variables: List of variables to substitute in the template
        from_phone: Sender phone number (defaults to TWILIO_WHATSAPP_NUMBER)
        save_to_db: Whether to save the message to the database
    
    Returns:
        SendMessageResult with success status and message details
    """
    # Resolve template
    if isinstance(template, str):
        template_obj = WhatsAppTemplate.objects.get(slug=template)
    elif isinstance(template, int):
        template_obj = WhatsAppTemplate.objects.get(pk=template)
    else:
        template_obj = template
    
    # Render the template
    rendered_body = template_obj.render(variables)
    
    config = get_twilio_config()
    if from_phone is None:
        from_phone = config["whatsapp_number"]
    
    to_formatted = format_whatsapp_number(to_phone)
    from_formatted = format_whatsapp_number(from_phone)
    
    # Create conversation and message record first
    message_obj = None
    if save_to_db:
        conversation = get_or_create_conversation(
            participant_phone=to_phone,
            twilio_phone=from_phone,
        )
        message_obj = WhatsAppMessage.objects.create(
            conversation=conversation,
            body=rendered_body,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.QUEUED,
            metadata={
                "template_slug": template_obj.slug,
                "template_variables": variables,
            }
        )
    
    try:
        client = get_twilio_client()
        
        # If template has a Content SID, use it; otherwise send as regular message
        if template_obj.content_sid:
            # Using Twilio Content API for templates
            twilio_message = client.messages.create(
                from_=from_formatted,
                to=to_formatted,
                content_sid=template_obj.content_sid,
                content_variables=dict(enumerate(variables, start=1)),
            )
        else:
            # Fallback to regular message with rendered body
            twilio_message = client.messages.create(
                from_=from_formatted,
                to=to_formatted,
                body=rendered_body,
            )
        
        if message_obj:
            message_obj.twilio_sid = twilio_message.sid
            message_obj.status = MessageStatus.SENT
            message_obj.sent_at = timezone.now()
            message_obj.save(update_fields=[
                "twilio_sid", "status", "sent_at", "updated_at"
            ])
        
        logger.info(
            f"WhatsApp template message sent. SID: {twilio_message.sid}, "
            f"Template: {template_obj.slug}, To: {to_phone}"
        )
        
        return SendMessageResult(
            success=True,
            message=message_obj,
            twilio_sid=twilio_message.sid,
        )
    
    except TwilioRestException as e:
        logger.error(
            f"Failed to send WhatsApp template message. "
            f"Error: {e.code} - {e.msg}"
        )
        
        if message_obj:
            message_obj.status = MessageStatus.FAILED
            message_obj.error_code = str(e.code)
            message_obj.error_message = e.msg
            message_obj.save(update_fields=[
                "status", "error_code", "error_message", "updated_at"
            ])
        
        return SendMessageResult(
            success=False,
            message=message_obj,
            error_code=str(e.code),
            error_message=e.msg,
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error sending template message: {e}")
        
        if message_obj:
            message_obj.status = MessageStatus.FAILED
            message_obj.error_message = str(e)
            message_obj.save(update_fields=[
                "status", "error_message", "updated_at"
            ])
        
        return SendMessageResult(
            success=False,
            message=message_obj,
            error_message=str(e),
        )


# -----------------------------------------------------------------------------
# Message Retrieval from Twilio API
# -----------------------------------------------------------------------------
def fetch_message_status(twilio_sid: str) -> Dict[str, Any]:
    """
    Fetch the current status of a message from Twilio API.
    
    Returns a dict with status info or error details.
    """
    try:
        client = get_twilio_client()
        message = client.messages(twilio_sid).fetch()
        
        return {
            "sid": message.sid,
            "status": message.status,
            "error_code": message.error_code,
            "error_message": message.error_message,
            "date_sent": message.date_sent,
            "date_updated": message.date_updated,
        }
    
    except TwilioRestException as e:
        return {
            "error": True,
            "error_code": str(e.code),
            "error_message": e.msg,
        }


def sync_message_status(message: Union[int, WhatsAppMessage]) -> WhatsAppMessage:
    """
    Sync a message's status from Twilio API.
    """
    if isinstance(message, int):
        message = WhatsAppMessage.objects.get(pk=message)
    
    if not message.twilio_sid:
        return message
    
    status_info = fetch_message_status(message.twilio_sid)
    
    if status_info.get("error"):
        return message
    
    # Map Twilio status to our MessageStatus
    twilio_status_map = {
        "queued": MessageStatus.QUEUED,
        "sending": MessageStatus.SENDING,
        "sent": MessageStatus.SENT,
        "delivered": MessageStatus.DELIVERED,
        "read": MessageStatus.READ,
        "failed": MessageStatus.FAILED,
        "undelivered": MessageStatus.FAILED,
    }
    
    new_status = twilio_status_map.get(
        status_info["status"], 
        message.status
    )
    
    update_fields = ["updated_at"]
    
    if new_status != message.status:
        message.status = new_status
        update_fields.append("status")
        
        if new_status == MessageStatus.DELIVERED and not message.delivered_at:
            message.delivered_at = timezone.now()
            update_fields.append("delivered_at")
        
        if new_status == MessageStatus.READ and not message.read_at:
            message.read_at = timezone.now()
            update_fields.append("read_at")
    
    if status_info.get("error_code"):
        message.error_code = str(status_info["error_code"])
        message.error_message = status_info.get("error_message", "")
        update_fields.extend(["error_code", "error_message"])
    
    message.save(update_fields=update_fields)
    return message


# -----------------------------------------------------------------------------
# Convenience Functions for Notifications
# -----------------------------------------------------------------------------
def send_notification(
    to_phone: str,
    message: str,
    **kwargs,
) -> SendMessageResult:
    """
    Simplified function to send a notification message.
    Useful for quick notifications and reminders.
    
    This is a convenience wrapper around send_whatsapp_message.
    """
    return send_whatsapp_message(
        to_phone=to_phone,
        body=message,
        **kwargs,
    )


def send_reminder(
    to_phone: str,
    reminder_text: str,
    template_slug: Optional[str] = None,
    template_variables: Optional[List[str]] = None,
    **kwargs,
) -> SendMessageResult:
    """
    Send a reminder message, optionally using a template.
    """
    if template_slug and template_variables is not None:
        return send_template_message(
            to_phone=to_phone,
            template=template_slug,
            variables=template_variables,
            **kwargs,
        )
    
    return send_whatsapp_message(
        to_phone=to_phone,
        body=reminder_text,
        **kwargs,
    )
