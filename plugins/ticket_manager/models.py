from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator
from base_modules.attachment.models import Attachment
from base_modules.user_manager.models import User
from base_modules.workspace.models import Workspace
from plugins.project_manager.models import Project

# --- Reuse delle tue scelte esistenti ---
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

TYPE_TICKET = (
    ('bug', 'Bug'),
    ('feature', 'Feature'),
    ('evo', 'Evolutiva'),
    ('check', 'Check'),
    ('aggiornamento', 'Aggiornamento'),
)

TASK_STATUS_CHOICES = (
    ('todo', 'To Do'),
    ('in_progress', 'In corso'),
    ('blocked', 'Bloccato'),
    ('done', 'Completato'),
    ('canceled', 'Annullato'),
)


class Ticket(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(max_length=2000, verbose_name="Description")

    client = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='cliente',
        blank=True, null=True, verbose_name="Client"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='progetto', verbose_name="Project"
    )
    assignees = models.ManyToManyField(
        User, related_name='assegnatario', blank=True, verbose_name="Assignees",
        limit_choices_to={'permission__in': [50, 100]}
    )

    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, blank=True, null=True, verbose_name="Priority"
    )
    hours_estimation = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="Hours estimation"
    )
    opening_date = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Opening date")
    closing_date = models.DateTimeField(null=True, blank=True, verbose_name="Closing date")
    cost_estimation = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cost"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open', blank=True, null=True
    )
    expected_resolution_date = models.DateTimeField(blank=True, null=True)
    expected_action = models.CharField(
        verbose_name="Comportamento atteso", validators=[MinLengthValidator(2)],
        max_length=1000, blank=True, null=True
    )
    real_action = models.CharField(
        verbose_name="Comportamento vero", validators=[MinLengthValidator(2)],
        max_length=1000, blank=True, null=True
    )
    attachments = models.ManyToManyField(Attachment, related_name='ticket_attachments', blank=True)
    ticket_workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name='workspace',
        blank=True, null=True, verbose_name="Workspace"
    )
    ticket_linked = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='linked_ticket',
        blank=True, null=True, verbose_name="Linked Ticket"
    )
    ticket_type = models.CharField(
        max_length=20, choices=TYPE_TICKET, default='bug', blank=True, null=True
    )
    payments_status = models.BooleanField(default=False)

    # Opzionale: aggiunta per future SLA o chiusure automatiche
    sla_due_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """
        Auto-calcola il costo stimato del ticket in base alla priorità e
        al costo orario del progetto. Se il ticket è di tipo 'bug', il costo è 0€.
        """
        # Se la tipologia è BUG, il costo è sempre zero
        if self.ticket_type == 'bug':
            self.cost_estimation = 0
        else:
            # Calcolo solo se ci sono minuti e un progetto associato
            if self.hours_estimation and self.project:
                # Converti minuti in ore (es: 90 minuti -> 1.5 ore)
                hours = float(self.hours_estimation) / 60.0

                # Determina il costo orario in base alla priorità
                hourly_rate = None
                if self.priority == 'low':
                    hourly_rate = self.project.hours_quote_min
                elif self.priority == 'medium':
                    hourly_rate = self.project.hours_quote_mid
                elif self.priority == 'high':
                    hourly_rate = self.project.hours_quote_max
                else:
                    hourly_rate = self.project.hours_quote_mid

                # Se il progetto ha il valore richiesto
                if hourly_rate:
                    self.cost_estimation = hours * float(hourly_rate)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ('opening_date',)

    @property
    def all_tasks_done(self):
        qs = self.tasks.all()
        return qs.exists() and not qs.exclude(status='done').exists()


class Message(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticket')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
    text = models.CharField(verbose_name="Testo del Messaggio", max_length=500000)
    insert_date = models.DateTimeField(verbose_name="Data Inserimento", auto_now_add=True)
    attachments = models.ManyToManyField(Attachment, related_name='message_attachments', blank=True)

    def __str__(self):
        return f"{self.ticket.title} ({self.id})"

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ('insert_date',)


class Task(models.Model):
    """
    Rappresenta un'unità di lavoro interna legata a un progetto o a un ticket.
    Serve a scomporre un ticket (anche evolutivo) in attività operative.
    """
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='tasks',
        blank=True, null=True, help_text="Ticket di origine, se deriva da richiesta cliente"
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='assigned_tasks',
        blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=TASK_STATUS_CHOICES, default='todo', db_index=True
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium', db_index=True
    )
    estimate_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True
    )
    customer_visible = models.BooleanField(default=False)
    attachments = models.ManyToManyField(Attachment, related_name='task_attachments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['project', 'status']),
        ]

    def __str__(self):
        prefix = f"[{self.ticket_id}]" if self.ticket_id else "[no-ticket]"
        return f"{prefix} {self.title}"
