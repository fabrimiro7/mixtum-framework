import logging
from typing import Dict, List, Optional

from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from base_modules.mailer.services import send_templated_email

from .models import Ticket

logger = logging.getLogger(__name__)


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


def _get_ticket_recipients(ticket: Ticket) -> List[str]:
    recipients = set()
    if ticket.client and ticket.client.email:
        recipients.add(ticket.client.email)
    assignees_qs = ticket.assignees.exclude(email__isnull=True).exclude(email__exact="")
    recipients.update(assignees_qs.values_list("email", flat=True))
    return list(recipients)


def _dispatch_notification(template_slug: str, recipients: List[str], context: Dict):
    if not recipients:
        return
    try:
        send_templated_email(
            template_slug=template_slug,
            to=recipients,
            context=context,
            fail_silently=True,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "Ticket notification `%s` failed for recipients %s",
            template_slug,
            recipients,
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
    recipients = _get_ticket_recipients(instance)
    if created:
        context = _get_ticket_context(instance)
        _dispatch_notification("ticket_created", recipients, context)
        return

    prev_status = getattr(instance, "_previous_status", None)
    if prev_status and prev_status != instance.status:
        context = _get_ticket_context(instance)
        context["previous_status"] = prev_status
        context["new_status"] = instance.status
        _dispatch_notification("ticket_status_changed", recipients, context)


@receiver(m2m_changed, sender=Ticket.assignees.through)
def _ticket_assignees_changed(sender, instance, action, pk_set, **kwargs):
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    recipients = _get_ticket_recipients(instance)
    context = _get_ticket_context(instance)
    context["assignee_action"] = action
    if pk_set:
        context["changed_assignees"] = list(pk_set)
    _dispatch_notification("ticket_assignees_changed", recipients, context)
