from django.db import models
from base_modules.user_manager.models import User
from plugins.ticket_manager.models import Ticket
from django.core.validators import MinLengthValidator
from  plugins.project_manager.models import Project


class Report(models.Model):
    report_title = models.CharField(verbose_name="Titolo report", validators=[MinLengthValidator(2)], max_length=1000, null=True)
    report_description = models.CharField(verbose_name="Descrizione report", validators=[MinLengthValidator(2)], max_length=1000, null=True)
    report_ticket = models.ForeignKey(Ticket, verbose_name="Ticket", on_delete=models.CASCADE, null=True, blank=True)
    report_project = models.ForeignKey(Project, verbose_name="Progetto", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Report'
        ordering = ('report_title',)