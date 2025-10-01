from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

class Logs(models.Model):
    """
    Modello per salvare i log delle eccezioni.
    """
    message = models.TextField(verbose_name="Messaggio di errore")
    exception_type = models.CharField(max_length=255, verbose_name="Tipo di eccezione", blank=True, null=True)
    category = models.CharField(max_length=100, verbose_name="Categoria", blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Data e ora")
    extra_data = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name="Dati aggiuntivi (es. stack trace)"
    )

    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Log: {self.exception_type} ({self.category}) - {self.timestamp}"
    
def create_log(message, exception_type=None, category=None, extra_data=None):
    """
    Funzione helper per creare e salvare un'istanza del modello Logs.
    
    Args:
        message (str): Il messaggio di errore principale.
        exception_type (str, optional): Il tipo di eccezione. Defaults to None.
        category (str, optional): La categoria del log. Defaults to None.
        extra_data (dict, optional): Un dizionario con dati aggiuntivi. Defaults to None.
    """
    Logs.objects.create(
        message=message,
        exception_type=exception_type,
        category=category,
        extra_data=extra_data
    )
