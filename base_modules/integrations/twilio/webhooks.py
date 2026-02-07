"""
Twilio WhatsApp Webhook Handlers

Handles incoming webhook callbacks from Twilio:
- Incoming messages
- Message status updates (delivered, read, failed)
"""
import logging
import hmac
import hashlib
from functools import wraps

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from twilio.request_validator import RequestValidator

from .models import (
    WhatsAppMessage,
    WhatsAppConversation,
    MessageDirection,
    MessageStatus,
)
from .services import (
    get_or_create_conversation,
    extract_phone_number,
)


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Webhook Security
# -----------------------------------------------------------------------------
def validate_twilio_request(func):
    """
    Decorator to validate that requests are actually from Twilio.
    Uses Twilio's request signing mechanism.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Skip validation in DEBUG mode if configured
        if getattr(settings, "DEBUG", False) and getattr(
            settings, "TWILIO_SKIP_SIGNATURE_VALIDATION", False
        ):
            return func(request, *args, **kwargs)
        
        auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        if not auth_token:
            logger.error("TWILIO_AUTH_TOKEN not configured")
            return HttpResponse("Server configuration error", status=500)
        
        validator = RequestValidator(auth_token)
        
        # Get the full URL that Twilio called
        request_url = request.build_absolute_uri()
        
        # Get the signature from headers
        twilio_signature = request.headers.get("X-Twilio-Signature", "")
        
        # Validate the request
        post_vars = dict(request.POST.items())
        
        if not validator.validate(request_url, post_vars, twilio_signature):
            logger.warning(
                f"Invalid Twilio signature. URL: {request_url}, "
                f"Signature: {twilio_signature}"
            )
            return HttpResponse("Invalid signature", status=403)
        
        return func(request, *args, **kwargs)
    
    return wrapper


# -----------------------------------------------------------------------------
# Incoming Message Webhook
# -----------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
@validate_twilio_request
def whatsapp_incoming(request):
    """
    Handle incoming WhatsApp messages from Twilio.
    
    Twilio sends POST requests with the following parameters:
    - MessageSid: Unique message identifier
    - From: Sender phone number (whatsapp:+1234567890)
    - To: Recipient phone number (your Twilio number)
    - Body: Message text
    - NumMedia: Number of media attachments
    - MediaUrl0, MediaUrl1, etc.: Media URLs
    - MediaContentType0, etc.: Media content types
    - ProfileName: Sender's WhatsApp profile name
    """
    try:
        # Extract data from the webhook
        message_sid = request.POST.get("MessageSid", "")
        from_number = request.POST.get("From", "")
        to_number = request.POST.get("To", "")
        body = request.POST.get("Body", "")
        profile_name = request.POST.get("ProfileName", "")
        num_media = int(request.POST.get("NumMedia", 0))
        
        # Extract phone numbers
        participant_phone = extract_phone_number(from_number)
        twilio_phone = extract_phone_number(to_number)
        
        # Collect media URLs
        media_urls = []
        media_types = []
        for i in range(num_media):
            media_url = request.POST.get(f"MediaUrl{i}")
            media_type = request.POST.get(f"MediaContentType{i}")
            if media_url:
                media_urls.append(media_url)
            if media_type:
                media_types.append(media_type)
        
        # Check if we already have this message (idempotency)
        if WhatsAppMessage.objects.filter(twilio_sid=message_sid).exists():
            logger.info(f"Duplicate message received: {message_sid}")
            return HttpResponse("OK", status=200)
        
        # Get or create conversation
        conversation = get_or_create_conversation(
            participant_phone=participant_phone,
            twilio_phone=twilio_phone,
            participant_name=profile_name,
        )
        
        # Create the message record
        message = WhatsAppMessage.objects.create(
            conversation=conversation,
            twilio_sid=message_sid,
            body=body,
            media_urls=media_urls,
            media_content_types=media_types,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            metadata={
                "profile_name": profile_name,
                "raw_from": from_number,
                "raw_to": to_number,
            }
        )
        
        logger.info(
            f"Received WhatsApp message. SID: {message_sid}, "
            f"From: {participant_phone}, Body length: {len(body)}"
        )
        
        # Return TwiML response (empty response is fine for just receiving)
        return HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            content_type="text/xml",
        )
    
    except Exception as e:
        logger.exception(f"Error processing incoming WhatsApp message: {e}")
        return HttpResponse("Error", status=500)


# -----------------------------------------------------------------------------
# Message Status Webhook
# -----------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
@validate_twilio_request
def whatsapp_status(request):
    """
    Handle message status updates from Twilio.
    
    Twilio sends status updates with:
    - MessageSid: The message identifier
    - MessageStatus: New status (queued, sending, sent, delivered, read, failed)
    - ErrorCode: Error code if failed
    - ErrorMessage: Error message if failed
    """
    try:
        message_sid = request.POST.get("MessageSid", "")
        new_status = request.POST.get("MessageStatus", "")
        error_code = request.POST.get("ErrorCode", "")
        error_message = request.POST.get("ErrorMessage", "")
        
        # Map Twilio status to our status
        status_map = {
            "queued": MessageStatus.QUEUED,
            "sending": MessageStatus.SENDING,
            "sent": MessageStatus.SENT,
            "delivered": MessageStatus.DELIVERED,
            "read": MessageStatus.READ,
            "failed": MessageStatus.FAILED,
            "undelivered": MessageStatus.FAILED,
        }
        
        mapped_status = status_map.get(new_status)
        if not mapped_status:
            logger.warning(f"Unknown message status: {new_status}")
            return HttpResponse("OK", status=200)
        
        # Find and update the message
        try:
            message = WhatsAppMessage.objects.get(twilio_sid=message_sid)
        except WhatsAppMessage.DoesNotExist:
            logger.warning(f"Status update for unknown message: {message_sid}")
            return HttpResponse("OK", status=200)
        
        # Update the message status
        update_fields = ["status", "updated_at"]
        message.status = mapped_status
        
        if mapped_status == MessageStatus.DELIVERED and not message.delivered_at:
            message.delivered_at = timezone.now()
            update_fields.append("delivered_at")
        
        if mapped_status == MessageStatus.READ and not message.read_at:
            message.read_at = timezone.now()
            update_fields.append("read_at")
        
        if error_code:
            message.error_code = error_code
            message.error_message = error_message
            update_fields.extend(["error_code", "error_message"])
        
        message.save(update_fields=update_fields)
        
        logger.info(
            f"Updated message status. SID: {message_sid}, Status: {new_status}"
        )
        
        return HttpResponse("OK", status=200)
    
    except Exception as e:
        logger.exception(f"Error processing message status update: {e}")
        return HttpResponse("Error", status=500)
