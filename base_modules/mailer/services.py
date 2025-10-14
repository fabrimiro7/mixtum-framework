from typing import Iterable, Optional, Dict, Any, List, Union
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Template, Context
from django.utils import timezone
from django.conf import settings
from .models import Email as EmailModel, EmailTemplate, EmailStatus

def _render_from_template(subject_tmpl: str, html_tmpl: str, text_tmpl: str, context: dict):
    ctx = Context(context or {})
    subj = Template(subject_tmpl).render(ctx).strip()
    html = Template(html_tmpl).render(ctx)
    text = Template(text_tmpl).render(ctx).strip() if text_tmpl else ""
    return subj, text, html

def render_email_instance(email: EmailModel) -> EmailModel:
    """
    Applica il template (se presente) e popola subject/body_text/body_html sull'istanza non salvata.
    Non salva a DB: restituisce l'istanza modificata.
    """
    if email.template:
        subject, text, html = _render_from_template(
            email.template.subject_template,
            email.template.html_template,
            email.template.text_template or "",
            email.context or {},
        )
        # Subject/body diretti hanno priorità se già inseriti manualmente
        email.subject = email.subject or subject
        email.body_text = email.body_text or text
        email.body_html = email.body_html or html
    return email

def send_email(
    email: Union[int, EmailModel],
    context_override: Optional[dict] = None,
    fail_silently: bool = False,
    connection_kwargs: Optional[dict] = None,
) -> bool:
    """
    Invia una Email (istanza o id) usando EmailMultiAlternatives.
    Aggiorna status/sent_at/retries/last_error.
    Ritorna True/False.
    """
    if isinstance(email, int):
        email = EmailModel.objects.select_related("template").get(pk=email)

    if context_override:
        email.context = {**(email.context or {}), **context_override}

    render_email_instance(email)

    from_email = email.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    msg = EmailMultiAlternatives(
        subject=email.subject or "",
        body=email.body_text or "",
        from_email=from_email,
        to=email.to or [],
        cc=email.cc or [],
        bcc=email.bcc or [],
        connection=get_connection(**(connection_kwargs or {})),
    )
    if email.body_html:
        msg.attach_alternative(email.body_html, "text/html")

    # Allegati
    for att in email.attachments.all():
        # name/mimetype opzionali: django li deduce se non forniti
        msg.attach(att.name or att.file.name, att.file.read(), att.mimetype or None)

    # invio
    email.status = EmailStatus.SENDING
    email.retries = (email.retries or 0) + 1
    email.save(update_fields=["status", "retries", "updated_at"])

    try:
        sent = msg.send()
        if sent > 0:
            email.status = EmailStatus.SENT
            email.sent_at = timezone.now()
            email.last_error = ""
            email.save(update_fields=["status", "sent_at", "last_error", "updated_at"])
            return True
        else:
            raise RuntimeError("Email backend did not send the message.")
    except Exception as e:
        email.status = EmailStatus.FAILED
        email.last_error = str(e)
        email.save(update_fields=["status", "last_error", "updated_at"])
        if not fail_silently:
            raise
        return False

def send_templated_email(
    *,
    template_slug: str,
    to: List[str],
    context: Dict[str, Any],
    subject_override: Optional[str] = None,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[tuple]] = None,
    fail_silently: bool = False,
) -> EmailModel:
    """
    Scorciatoia per creare + inviare una mail a partire da un template.
    attachments: lista di tuple (filename, content_bytes, mimetype)
    Ritorna l'istanza Email salvata.
    """
    tmpl = EmailTemplate.objects.get(slug=template_slug)
    email = EmailModel.objects.create(
        from_email=from_email,
        to=to or [],
        cc=cc or [],
        bcc=bcc or [],
        subject=subject_override or "",
        template=tmpl,
        context=context or {},
        status=EmailStatus.QUEUED,
    )

    # allegati in memoria (facoltativi)
    if attachments:
        from django.core.files.base import ContentFile
        for (filename, content, mimetype) in attachments:
            from .models import EmailAttachment
            EmailAttachment.objects.create(
                email=email,
                file=ContentFile(content, name=filename),
                name=filename,
                mimetype=mimetype or "",
            )

    # invia subito (puoi delegare a Celery se vuoi)
    send_email(email, fail_silently=fail_silently)
    return email
