# email_manager/tasks.py
from __future__ import annotations

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Email as EmailModel, EmailStatus
from .services import send_email


@shared_task
def enqueue_due_emails(batch_size: int = 200) -> int:
    """
    Dispatcher: prende le email dovute e le mette in lavorazione.
    - Seleziona Email QUEUED non inviate e "due" (scheduled_at NULL o <= now)
    - Le "prenota" (QUEUED -> SENDING) in modo atomico per evitare doppioni
    - Enqueue di send_email_task(email_id)

    Ritorna il numero di email enqueued.
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
        # Claim atomico (evita che due dispatcher/worker prendano la stessa email)
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
    Invia una singola Email usando il tuo service.send_email.

    Regole:
    - Idempotenza: se già sent_at valorizzato -> exit
    - Se non è in SENDING (o QUEUED in casi di recovery), non la tocca
    - In caso di errore:
        - se Celery ritenterà -> status torna a QUEUED (così è "retryable" e coerente a DB)
        - se retry esauriti -> status resta FAILED (lasciato dal service)
    """
    now = timezone.now()

    # 1) Pre-check + lock riga
    with transaction.atomic():
        try:
            email_obj = EmailModel.objects.select_for_update().get(pk=email_id)
        except EmailModel.DoesNotExist:
            return

        if email_obj.sent_at:
            return

        # Non inviare se non eleggibile
        if email_obj.status in (EmailStatus.DRAFT, EmailStatus.SENT):
            return

        # Scheduled in futuro: rimetto QUEUED e stop (non è un errore)
        if email_obj.scheduled_at and email_obj.scheduled_at > now:
            if email_obj.status != EmailStatus.QUEUED:
                email_obj.status = EmailStatus.QUEUED
                email_obj.save(update_fields=["status", "updated_at"])
            return

        # Se non è SENDING, evita invii “fuori flusso”
        # (consente comunque QUEUED in scenari di recovery manuale)
        if email_obj.status not in (EmailStatus.SENDING, EmailStatus.QUEUED):
            return

        # Normalizza a SENDING prima di inviare
        if email_obj.status != EmailStatus.SENDING:
            email_obj.status = EmailStatus.SENDING
            email_obj.save(update_fields=["status", "updated_at"])

    # 2) Invio fuori transazione (I/O)
    try:
        # Usiamo fail_silently=False per far emergere l'eccezione e usare retry Celery
        # Nota: il tuo service salva già status=SENT/FAILED e sent_at/last_error.
        send_email(email_id, fail_silently=False)

    except Exception as exc:
        # 3) Se Celery ritenterà, non voglio lasciare FAILED "temporaneo":
        # riporto a QUEUED (ma conservando last_error già scritto dal service).
        will_retry = self.request.retries < self.max_retries

        if will_retry:
            with transaction.atomic():
                try:
                    email_obj = EmailModel.objects.select_for_update().get(pk=email_id)
                except EmailModel.DoesNotExist:
                    return

                # Se qualcuno l'ha già segnata come inviata nel frattempo, stop
                if email_obj.sent_at:
                    return

                # Ri-queue: l'email è fallita, ma è ancora retryable
                email_obj.status = EmailStatus.QUEUED
                email_obj.save(update_fields=["status", "updated_at"])

            raise self.retry(exc=exc)

        # Retry esauriti: lasciamo FAILED (già impostato dal service) e usciamo
        return
