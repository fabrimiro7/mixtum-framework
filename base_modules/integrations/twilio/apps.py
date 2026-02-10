from django.apps import AppConfig


class TwilioConfig(AppConfig):
    name = 'base_modules.integrations.twilio'
    verbose_name = "Twilio WhatsApp Integration"
    
    def ready(self):
        # Import signals if needed
        pass
