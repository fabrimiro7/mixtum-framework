from .models import ConfigSetting
from django.core.exceptions import ObjectDoesNotExist

def get_config(key, default=None):
    """
    Restituisce il valore della configurazione per la chiave data.
    Se la chiave non esiste, restituisce il valore di default.
    """
    try:
        setting = ConfigSetting.objects.get(key=key)
        return setting.value
    except ObjectDoesNotExist:
        return default
