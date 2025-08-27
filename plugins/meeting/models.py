from django.db import models
from base_modules.user_manager.models import User
from django.core.validators import MinLengthValidator
# Create your models here.

class Meeting(models.Model):
    title = models.CharField(verbose_name="Titolo", max_length=1000, null=True, blank=True)
    insert_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insert_by')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cliente_meeting')
    start_date = models.DateTimeField(verbose_name="Data inizio", null=True, blank=True)
    end_date = models.DateTimeField(verbose_name="Data fine", null=True, blank=True)
    note = models.CharField(verbose_name="Note", max_length=250, null=True, blank=True)
    link_streaming = models.CharField(verbose_name="Link streaming", max_length=1000, null=True, blank=True)
    insert_date = models.DateField(verbose_name="Data Inserimento", null=True, blank=True, auto_now_add=True)
    users_meeting = models.ManyToManyField(User, related_name='user_meeting', blank=True, verbose_name="Utenti Meeting")
    included_in_subscription = models.BooleanField(default=False, verbose_name="Incluso in abbonamento")
    duration = models.DurationField(verbose_name="Durata", null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo", null=True, blank=True)
    ai_summary = models.TextField(verbose_name="AI Summary", null=True, blank=True, validators=[MinLengthValidator(2)])

    def __str__(self):
        try:
            string_output = "%s" % self.title
        except Exception:
            string_output = "Meeting"
        return string_output

    class Meta:
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meeting'
        ordering = ('start_date',)