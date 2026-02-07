import logging
from typing import Dict, List, Optional

from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from base_modules.mailer.services import send_individual_templated_emails
from base_modules.user_manager.models import User

from .models import Ticket

logger = logging.getLogger(__name__)


def _get_status_display_message(status: Optional[str]) -> str:
    """
    Converte un valore tecnico di stato in un messaggio user-friendly in italiano.
    
    Args:
        status: Valore tecnico dello stato (es. 'in_progress', 'resolved')
    
    Returns:
        Messaggio user-friendly in italiano, o il valore originale se non riconosciuto
    """
    if not status:
        return status or ""
    
    status_mapping = {
        'open': 'Il ticket è stato aperto',
        'in_progress': 'Ticket preso in carico',
        'resolved': 'Il ticket è stato risolto',
        'closed': 'Il ticket è stato chiuso',
    }
    
    return status_mapping.get(status, status)


def _get_ticket_context(ticket: Ticket) -> Dict[str, Dict[str, Optional[str]]]:
    assignee_names = [
        assignee.get_name() or assignee.email
        for assignee in ticket.assignees.all()
        if assignee.email
    ]
    client_name = ticket.client.get_name() if ticket.client else ""
    project_title = ticket.project.title if ticket.project else ""
    return {
        "ticket": {
            "id": ticket.id,
            "title": ticket.title,
            "status": ticket.status,
            "status_display": ticket.get_status_display(),
            "project": project_title,
            "client_name": client_name,
            "assignees": assignee_names,
        }
    }


def _get_ticket_recipients(ticket: Ticket, client_email: bool = True) -> List[str]:
    """
    Versione legacy che restituisce solo le email (per retrocompatibilità).
    """
    recipients = set()
    if client_email:
        if ticket.client and ticket.client.email:
            recipients.add(ticket.client.email)
    assignees_qs = ticket.assignees.exclude(email__isnull=True).exclude(email__exact="")
    recipients.update(assignees_qs.values_list("email", flat=True))
    return list(recipients)


def _get_ticket_recipients_with_data(ticket: Ticket, include_client: bool = True) -> List[Dict[str, Optional[str]]]:
    """
    Restituisce i destinatari con i loro dati completi (email, nome, cognome)
    per l'invio di email personalizzate individuali.
    
    Args:
        ticket: il ticket di riferimento
        include_client: se True, include il client tra i destinatari
    
    Returns:
        Lista di dizionari con 'email', 'first_name', 'last_name', 'name'
    """
    recipients = []
    seen_emails = set()
    
    # Aggiungi il client se richiesto
    if include_client and ticket.client and ticket.client.email:
        email = ticket.client.email.lower()
        if email not in seen_emails:
            seen_emails.add(email)
            recipients.append({
                'email': ticket.client.email,
                'first_name': ticket.client.first_name or '',
                'last_name': ticket.client.last_name or '',
                'name': ticket.client.get_name() or ticket.client.email,
                'is_client': True,
                'is_assignee': False,
            })
    
    # Aggiungi gli assignees
    assignees_qs = ticket.assignees.exclude(email__isnull=True).exclude(email__exact="")
    for assignee in assignees_qs:
        email = assignee.email.lower()
        if email not in seen_emails:
            seen_emails.add(email)
            recipients.append({
                'email': assignee.email,
                'first_name': assignee.first_name or '',
                'last_name': assignee.last_name or '',
                'name': assignee.get_name() or assignee.email,
                'is_client': False,
                'is_assignee': True,
            })
    
    return recipients


def _dispatch_individual_notifications(
    template_slug: str,
    recipients: List[Dict[str, Optional[str]]],
    context: Dict
):
    """
    Invia notifiche email individuali a ciascun destinatario.
    Ogni destinatario riceve una email personalizzata con i propri dati.
    
    Args:
        template_slug: slug del template email
        recipients: lista di dizionari con dati destinatario (email, first_name, last_name, name)
        context: contesto base condiviso tra tutte le email
    """
    if not recipients:
        return
    try:
        send_individual_templated_emails(
            template_slug=template_slug,
            recipients=recipients,
            base_context=context,
            fail_silently=True,
        )
    except Exception as exc:  # pragma: no cover
        recipient_emails = [r.get('email') for r in recipients]
        logger.exception(
            "Ticket notification `%s` failed for recipients %s",
            template_slug,
            recipient_emails,
            exc_info=exc,
        )


@receiver(pre_save, sender=Ticket)
def _cache_previous_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return
    try:
        previous = sender.objects.only("status").get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._previous_status = None
    else:
        instance._previous_status = previous.status


@receiver(post_save, sender=Ticket)
def _ticket_post_save(sender, instance, created, **kwargs):
    recipients = _get_ticket_recipients_with_data(instance)
    if created:
        context = _get_ticket_context(instance)
        _dispatch_individual_notifications("ticket_created", recipients, context)
        return

    prev_status = getattr(instance, "_previous_status", None)
    if prev_status and prev_status != instance.status:
        context = _get_ticket_context(instance)
        context["previous_status"] = prev_status
        context["new_status"] = instance.status
        context["previous_status_display"] = _get_status_display_message(prev_status)
        context["new_status_display"] = _get_status_display_message(instance.status)
        _dispatch_individual_notifications("ticket_status_changed", recipients, context)


@receiver(m2m_changed, sender=Ticket.assignees.through)
def _ticket_assignees_changed(sender, instance, action, pk_set, **kwargs):
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    recipients = _get_ticket_recipients_with_data(instance, include_client=False)
    context = _get_ticket_context(instance)
    context["assignee_action"] = action
    if pk_set:
        context["changed_assignees"] = list(pk_set)
    _dispatch_individual_notifications("ticket_assignees_changed", recipients, context)
