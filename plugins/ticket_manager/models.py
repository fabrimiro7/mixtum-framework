from django.db import models
from base_modules.attachment.models import Attachment
from base_modules.user_manager.models import User
from django.core.validators import MinLengthValidator
from base_modules.workspace.models import Workspace
from plugins.project_manager.models import *

PRIORITY_CHOICES = (
    ('low', 'Bassa'),
    ('medium', 'Media'),
    ('high', 'Alta'),
)

STATUS_CHOICES = (
    ('open', 'Aperto'),
    ('in_progress', 'In corso'),
    ('resolved', 'Risolto'),
    ('closed', 'Chiuso'),
)


class Ticket(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(max_length=2000, verbose_name="Description")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cliente', blank=True, null=True, verbose_name="Client")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='progetto', verbose_name="Project")
    assignees = models.ManyToManyField(User, related_name='assegnatario', blank=True, verbose_name="Assignees", limit_choices_to={'permission__in': [50, 100]})
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, blank=True, null=True, verbose_name="Priority")
    hours_estimation = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Hours estimation")
    opening_date = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Opening date")
    closing_date = models.DateTimeField(null=True, blank=True, verbose_name="Closing date")
    cost_estimation = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cost")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', blank=True, null=True)
    expected_resolution_date = models.DateTimeField(blank=True, null=True)
    expected_action = models.CharField(verbose_name="Comportamento atteso", validators=[MinLengthValidator(2)],
                                       max_length=1000, blank=True, null=True)
    real_action = models.CharField(verbose_name="Comportamento vero", validators=[MinLengthValidator(2)],
                                   max_length=1000, blank=True, null=True)
    attachments = models.ManyToManyField(Attachment, related_name='ticket_attachments', blank=True)
    ticket_workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='workspace', blank=True, null=True, verbose_name="Workspace")
    ticket_linked = models.ForeignKey('self', on_delete=models.CASCADE, related_name='linked_ticket', blank=True, null=True, verbose_name="Linked Ticket")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ('opening_date',)


class Message(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticket')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
    text = models.CharField(verbose_name="Testo del Messaggio", max_length=500000)
    insert_date = models.DateTimeField(verbose_name="Data Inserimento", auto_now_add=True)
    attachments = models.ManyToManyField(Attachment, related_name='message_attachments', blank=True)


    def __str__(self):
        string_return = "%s (%s)" % (self.ticket.title, self.id)
        return string_return

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ('insert_date',)
