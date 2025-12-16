# email_manager/tasks.py
from __future__ import annotations

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Email as EmailModel, EmailStatus
from .services import send_email_now  


@shared_task
def enqueue_due_emails(batch_size: int = 200) -> int:
    """
    Dispatcher: picks due emails and puts them in processing.
    - Selects QUEUED emails not sent and due (scheduled_at NULL or <= now)
    - Atomically claims them (QUEUED -> SENDING) to avoid duplicates
    - Enqueues send_email_task(email_id)

    Returns the number of emails enqueued.
    """
    now = timezone.now()

    ids = list(
        EmailModel.objects.filter(
            status=EmailStatus.QUEUED,
            sent_at__isnull=True,
        )
        .filter(Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now))
        .order_by("priority", "created_at")
        .values_list("id", flat=True)[:batch_size]
    )

    enqueued = 0
    for email_id in ids:
        updated = EmailModel.objects.filter(
            pk=email_id,
            status=EmailStatus.QUEUED,
            sent_at__isnull=True,
        ).update(status=EmailStatus.SENDING)

        if updated == 1:
            send_email_task.delay(email_id)
            enqueued += 1

    return enqueued


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_email_task(self, email_id: int) -> None:
    """
    Sends a single Email using services.send_email_now (real SMTP send).

    Rules:
    - Idempotent: if already sent_at -> exit
    - If not in SENDING (or QUEUED for manual recovery), it won't touch it
    - On error:
        - if Celery will retry -> status back to QUEUED
        - if retries exhausted -> leave FAILED (set by the service)
    """
    now = timezone.now()

    # 1) Pre-check + row lock
    with transaction.atomic():
        try:
            email_obj = EmailModel.objects.select_for_update().get(pk=email_id)
        except EmailModel.DoesNotExist:
            return

        if email_obj.sent_at:
            return

        if email_obj.status in (EmailStatus.DRAFT, EmailStatus.SENT):
            return

        if email_obj.scheduled_at and email_obj.scheduled_at > now:
            if email_obj.status != EmailStatus.QUEUED:
                email_obj.status = EmailStatus.QUEUED
                email_obj.save(update_fields=["status", "updated_at"])
            return

        if email_obj.status not in (EmailStatus.SENDING, EmailStatus.QUEUED):
            return

        if email_obj.status != EmailStatus.SENDING:
            email_obj.status = EmailStatus.SENDING
            email_obj.save(update_fields=["status", "updated_at"])

    # 2) Send outside transaction (I/O)
    try:
        # IMPORTANT: call the real sender, not the enqueue-only API
        send_email_now(email_id, fail_silently=False)

    except Exception as exc:
        will_retry = self.request.retries < self.max_retries

        if will_retry:
            with transaction.atomic():
                try:
                    email_obj = EmailModel.objects.select_for_update().get(pk=email_id)
                except EmailModel.DoesNotExist:
                    return

                if email_obj.sent_at:
                    return

                email_obj.status = EmailStatus.QUEUED
                email_obj.save(update_fields=["status", "updated_at"])

            raise self.retry(exc=exc)

        return
