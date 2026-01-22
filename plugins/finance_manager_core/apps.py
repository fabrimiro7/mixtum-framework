from django.apps import AppConfig


class FinanceManagerCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.finance_manager_core'
    verbose_name = 'Finance Manager - Core'

    def ready(self):
        # Import signals to ensure they are registered when the app is ready.
        from . import signals  # noqa: F401
