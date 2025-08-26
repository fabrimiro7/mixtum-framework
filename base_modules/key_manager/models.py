from django.db import models

class ConfigSetting(models.Model):
    """
    Modello per memorizzare chiavi e valori di configurazione dinamica.
    """
    key = models.CharField(max_length=100, help_text="La chiave della configurazione")
    value = models.TextField(help_text="Il valore della configurazione")
    description = models.TextField(blank=True, null=True, help_text="Descrizione della configurazione (opzionale)")

    def __str__(self):
        return self.key
