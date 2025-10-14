from django.db import models
from django.utils import timezone
from django.core.validators import validate_email
from django.contrib.postgres.fields import ArrayField  # opzionale: usato se hai Postgres
from django.conf import settings
from django.db.models import JSONField

class EmailStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    QUEUED = "queued", "Queued"
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"

class EmailTemplate(models.Model):
    """
    Template salvato a DB. Supporta soggetto, HTML e testo.
    Usa il motore template di Django ({{ name }}, {% if ... %}, ecc.).
    """
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    subject_template = models.TextField(help_text="Esempio: 'Ciao {{ user.first_name }}'")
    html_template = models.TextField(help_text="HTML con variabili: {{ ... }}")
    text_template = models.TextField(blank=True, default="", help_text="Fallback testuale (opzionale)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

def default_list():
    return []

class Email(models.Model):
    """
    Un'email (singolo invio). Può usare un template oppure contenuto diretto.
    - to/cc/bcc: liste di email come JSON (portabile su DB diversi).
    - context: dict per render dei template.
    """
    from_email = models.EmailField(blank=True, null=True, help_text="Se vuoto usa DEFAULT_FROM_EMAIL")
    to = JSONField(default=default_list, help_text="Lista destinatari, es: ['a@b.it','c@d.it']")
    cc = JSONField(default=default_list, blank=True)
    bcc = JSONField(default=default_list, blank=True)

    subject = models.CharField(max_length=255, blank=True, default="", help_text="Può essere valorizzato da template")
    body_text = models.TextField(blank=True, default="")
    body_html = models.TextField(blank=True, default="")

    template = models.ForeignKey(EmailTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    context = JSONField(default=dict, blank=True)

    status = models.CharField(max_length=16, choices=EmailStatus.choices, default=EmailStatus.DRAFT)
    priority = models.PositiveSmallIntegerField(default=3, help_text="1=alta, 5=bassa (puramente informativa)")

    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    retries = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        base = self.subject or "(senza oggetto)"
        return f"[{self.get_status_display()}] {base}"

    def clean(self):
        # Validazione semplice delle email
        for field in ("to", "cc", "bcc"):
            vals = getattr(self, field) or []
            if not isinstance(vals, list):
                raise ValueError(f"{field} deve essere una lista di stringhe")
            for v in vals:
                validate_email(v)

class EmailAttachment(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="email_attachments/")
    name = models.CharField(max_length=255, blank=True, default="")
    mimetype = models.CharField(max_length=100, blank=True, default="")
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, "size"):
            self.size = self.file.size
        super().save(*args, **kwargs)
