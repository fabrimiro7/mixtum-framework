# email_manager/service.py
from __future__ import annotations

from typing import Optional, Dict, Any, List, Union, Tuple
from email.utils import formataddr
import mimetypes

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import transaction
from django.template import Template, Context
from django.utils import timezone

from .models import Email as EmailModel, EmailTemplate, EmailStatus


# -----------------------------------------------------------------------------
# Template rendering helpers
# -----------------------------------------------------------------------------
def _render_from_template(
    subject_tmpl: str,
    html_tmpl: str,
    text_tmpl: str,
    context: dict,
) -> Tuple[str, str, str]:
    """
    Render subject/text/html using Django Template engine.
    """
    ctx = Context(context or {})
    subj = Template(subject_tmpl or "").render(ctx).strip()
    html = Template(html_tmpl or "").render(ctx)
    text = Template(text_tmpl or "").render(ctx).strip() if text_tmpl else ""
    return subj, text, html


def _get_from_address(email: EmailModel, from_name: Optional[str] = None) -> str:
    """
    Returns a properly formatted "From" header value, optionally using a display name.
    """
    base_email = (email.from_email or "").strip() or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    base_email = (base_email or "").strip()
    if not base_email:
        return ""

    display_name = (from_name or "").strip() or getattr(settings, "DEFAULT_FROM_DISPLAY_NAME", "")
    display_name = (display_name or "").strip()

    return formataddr((display_name, base_email)) if display_name else base_email


def render_email_instance(email: EmailModel) -> EmailModel:
    """
    Applies the template (if present) and populates subject/body_text/body_html on the instance.
    Does NOT save to DB: returns the modified instance.
    Direct subject/body values win if already set.
    """
    if email.template:
        subject, text, html = _render_from_template(
            email.template.subject_template,
            email.template.html_template,
            email.template.text_template or "",
            email.context or {},
        )
        email.subject = (email.subject or "").strip() or subject
        email.body_text = (email.body_text or "").strip() or text
        email.body_html = (email.body_html or "").strip() or html
    return email


# -----------------------------------------------------------------------------
# Internal: actual SMTP/API send (used by Celery task)
# -----------------------------------------------------------------------------
def send_email_now(
    email: Union[int, EmailModel],
    context_override: Optional[dict] = None,
    fail_silently: bool = False,
    connection_kwargs: Optional[dict] = None,
    from_name: Optional[str] = None,
) -> bool:
    """
    Sends an Email immediately using Django EmailMultiAlternatives.
    Intended to be called by Celery workers (task), not by request/HTTP codepaths.

    It updates status/sent_at/retries/last_error.
    Returns True/False.
    """
    if isinstance(email, int):
        email = (
            EmailModel.objects.select_related("template")
            .prefetch_related("attachments")
            .get(pk=email)
        )

    if context_override:
        email.context = {**(email.context or {}), **context_override}

    render_email_instance(email)

    from_email = _get_from_address(email, from_name)
    if not from_email:
        raise ValueError("Missing from_email and DEFAULT_FROM_EMAIL is not set.")

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

    # Attachments (robust file handling)
    for att in email.attachments.all():
        if not att.file:
            continue

        filename = att.name or (att.file.name.split("/")[-1] if att.file.name else "attachment")
        mimetype_value = (att.mimetype or "").strip()
        if not mimetype_value:
            guessed = mimetypes.guess_type(filename)[0]
            mimetype_value = guessed or "application/octet-stream"

        # Ensure the file is opened in binary mode and read from start
        try:
            att.file.open("rb")
            content = att.file.read()
        finally:
            try:
                att.file.close()
            except Exception:
                pass

        msg.attach(filename, content, mimetype_value)

    # Mark as SENDING and increment retries (attempt counter)
    email.status = EmailStatus.SENDING
    email.retries = (email.retries or 0) + 1
    email.save(update_fields=["status", "retries", "updated_at"])

    try:
        sent = msg.send(fail_silently=False)
        if sent > 0:
            email.status = EmailStatus.SENT
            email.sent_at = timezone.now()
            email.last_error = ""
            email.save(update_fields=["status", "sent_at", "last_error", "updated_at"])
            return True

        raise RuntimeError("Email backend did not send the message.")

    except Exception as e:
        email.status = EmailStatus.FAILED
        email.last_error = str(e)
        email.save(update_fields=["status", "last_error", "updated_at"])
        if not fail_silently:
            raise
        return False


# -----------------------------------------------------------------------------
# Public: enqueue (Celery-driven) orchestration
# -----------------------------------------------------------------------------
def enqueue_email(
    email: Union[int, EmailModel],
    *,
    schedule_at: Optional[Any] = None,
    dispatch_immediately_if_due: bool = True,
) -> EmailModel:
    """
    Marks an Email as QUEUED and optionally dispatches a Celery task if it's due now.

    - If schedule_at is provided, sets email.scheduled_at accordingly.
    - Always sets status to QUEUED (unless already SENT).
    - If dispatch_immediately_if_due=True and scheduled_at <= now (or NULL),
      it attempts an atomic claim (QUEUED -> SENDING) and dispatches send_email_task.delay(email_id).

    IMPORTANT:
    - This function does NOT send the email itself.
    - It requires email_manager.tasks.send_email_task to be available.
    """
    if isinstance(email, int):
        email_obj = EmailModel.objects.get(pk=email)
    else:
        email_obj = email

    if email_obj.sent_at or email_obj.status == EmailStatus.SENT:
        return email_obj

    if schedule_at is not None:
        email_obj.scheduled_at = schedule_at

    # Always queue (draft -> queued; failed -> queued if you allow manual re-queue)
    email_obj.status = EmailStatus.QUEUED
    email_obj.save(update_fields=["status", "scheduled_at", "updated_at"])

    if not dispatch_immediately_if_due:
        return email_obj

    now = timezone.now()
    if email_obj.scheduled_at and email_obj.scheduled_at > now:
        return email_obj

    # Atomic claim to avoid duplicates if multiple callers/dispatchers run
    with transaction.atomic():
        updated = EmailModel.objects.filter(
            pk=email_obj.pk,
            status=EmailStatus.QUEUED,
            sent_at__isnull=True,
        ).update(status=EmailStatus.SENDING)

    if updated == 1:
        # Import here to avoid circular imports at module load time
        from .tasks import send_email_task

        send_email_task.delay(email_obj.pk)

    return email_obj


def send_email(
    email: Union[int, EmailModel],
    context_override: Optional[dict] = None,
    fail_silently: bool = False,  # kept for signature compatibility; not used for enqueue
    connection_kwargs: Optional[dict] = None,  # kept for signature compatibility; not used for enqueue
    from_name: Optional[str] = None,  # kept for signature compatibility; not used for enqueue
) -> bool:
    """
    Enqueue-only API (does NOT send).

    This replaces the previous synchronous send_email behavior.
    It applies optional context overrides (saved to DB) and then queues the email.

    Returns True if the email was queued/accepted, False only if the Email does not exist.
    """
    try:
        if isinstance(email, int):
            email_obj = EmailModel.objects.get(pk=email)
        else:
            email_obj = email
    except EmailModel.DoesNotExist:
        return False

    if context_override:
        email_obj.context = {**(email_obj.context or {}), **context_override}
        email_obj.save(update_fields=["context", "updated_at"])

    enqueue_email(email_obj, dispatch_immediately_if_due=True)
    return True


def send_individual_templated_emails(
    *,
    template_slug: str,
    recipients: List[Dict[str, Any]],
    base_context: Dict[str, Any],
    subject_override: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    attachments: Optional[List[tuple]] = None,
    fail_silently: bool = False,
    scheduled_at: Optional[Any] = None,
    dispatch_immediately_if_due: bool = True,
) -> List[EmailModel]:
    """
    Invia email individuali personalizzate a ciascun destinatario.
    
    Invece di mandare una sola email con tutti in CC, questa funzione crea
    e accoda un'email separata per ogni destinatario, con il proprio contesto
    personalizzato (es. nome, cognome).
    
    Args:
        template_slug: slug del template da usare
        recipients: lista di dizionari, ognuno con:
            - 'email': indirizzo email del destinatario (obbligatorio)
            - 'first_name': nome (opzionale)
            - 'last_name': cognome (opzionale)
            - 'name': nome completo (opzionale, alternativo a first_name/last_name)
            - altri campi custom che verranno aggiunti al contesto
        base_context: contesto base condiviso tra tutte le email
        subject_override: oggetto personalizzato (opzionale)
        from_email: mittente (opzionale, usa DEFAULT_FROM_EMAIL se vuoto)
        from_name: nome visualizzato del mittente (opzionale)
        attachments: lista di tuple (filename, content_bytes, mimetype)
        fail_silently: se True, non solleva eccezioni in caso di errore
        scheduled_at: data/ora di invio programmato (opzionale)
        dispatch_immediately_if_due: se True, accoda immediatamente se l'invio è dovuto
    
    Returns:
        Lista di istanze EmailModel create
    """
    if not recipients:
        return []
    
    tmpl = EmailTemplate.objects.get(slug=template_slug)
    created_emails = []
    
    for recipient_data in recipients:
        recipient_email = recipient_data.get('email')
        if not recipient_email:
            continue
        
        # Costruisci il contesto personalizzato per questo destinatario
        recipient_context = {**(base_context or {})}
        
        # Aggiungi i dati del destinatario al contesto
        recipient_info = {
            'email': recipient_email,
            'first_name': recipient_data.get('first_name', ''),
            'last_name': recipient_data.get('last_name', ''),
            'name': recipient_data.get('name') or (
                f"{recipient_data.get('first_name', '')} {recipient_data.get('last_name', '')}".strip()
            ),
        }
        # Aggiungi eventuali altri campi custom dal recipient_data
        for key, value in recipient_data.items():
            if key not in ('email',):
                recipient_info[key] = value
        
        recipient_context['recipient'] = recipient_info
        
        # Crea l'email per questo destinatario
        email_obj = EmailModel.objects.create(
            from_email=from_email,
            to=[recipient_email],
            cc=[],  # Niente CC - email individuali
            bcc=[],
            subject=subject_override or "",
            template=tmpl,
            context=recipient_context,
            status=EmailStatus.QUEUED,
            scheduled_at=scheduled_at,
        )
        
        # Aggiungi allegati se presenti
        if attachments:
            from django.core.files.base import ContentFile
            from .models import EmailAttachment
            
            for (filename, content, mimetype_value) in attachments:
                EmailAttachment.objects.create(
                    email=email_obj,
                    file=ContentFile(content, name=filename),
                    name=filename,
                    mimetype=(mimetype_value or ""),
                )
        
        # Accoda l'email
        enqueue_email(email_obj, dispatch_immediately_if_due=dispatch_immediately_if_due)
        created_emails.append(email_obj)
    
    return created_emails


def send_templated_email(
    *,
    template_slug: str,
    to: List[str],
    context: Dict[str, Any],
    subject_override: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,  # stored in context if you want; or ignore
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[tuple]] = None,
    fail_silently: bool = False,  # kept for backward compatibility; enqueue-only
    scheduled_at: Optional[Any] = None,
    dispatch_immediately_if_due: bool = True,
) -> EmailModel:
    """
    Convenience: create + enqueue an email based on a template.
    This does NOT send immediately; it queues and optionally dispatches the Celery task if due.

    attachments: list of tuples (filename, content_bytes, mimetype)
    Returns the saved Email instance.
    """
    tmpl = EmailTemplate.objects.get(slug=template_slug)

    email_obj = EmailModel.objects.create(
        from_email=from_email,
        to=to or [],
        cc=cc or [],
        bcc=bcc or [],
        subject=subject_override or "",
        template=tmpl,
        context=context or {},
        status=EmailStatus.QUEUED,
        scheduled_at=scheduled_at,
    )

    # Optional in-memory attachments
    if attachments:
        from django.core.files.base import ContentFile
        from .models import EmailAttachment

        for (filename, content, mimetype_value) in attachments:
            EmailAttachment.objects.create(
                email=email_obj,
                file=ContentFile(content, name=filename),
                name=filename,
                mimetype=(mimetype_value or ""),
            )

    # Queue + optional immediate dispatch if due
    enqueue_email(email_obj, dispatch_immediately_if_due=dispatch_immediately_if_due)
    return email_obj
