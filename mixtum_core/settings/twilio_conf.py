"""
Twilio Configuration Settings

Loads Twilio credentials and settings from environment variables.
"""
import os

# Twilio Account Credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")

# Twilio WhatsApp Number (in E.164 format, e.g., +14155238886)
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

# Security: Skip signature validation in DEBUG mode (only for development!)
TWILIO_SKIP_SIGNATURE_VALIDATION = os.environ.get(
    "TWILIO_SKIP_SIGNATURE_VALIDATION", "0"
).lower() in ("1", "true", "yes")
