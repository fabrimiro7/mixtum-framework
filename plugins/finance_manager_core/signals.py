import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Transaction

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Transaction)
def cache_previous_status(sender, instance, **kwargs):
    """
    Cache the previous status before saving to detect status changes.
    """
    if not instance.pk:
        instance._previous_status = None
        instance._previous_payment_date = None
        return
    
    try:
        previous = sender.objects.only('status', 'payment_date').get(pk=instance.pk)
        instance._previous_status = previous.status
        instance._previous_payment_date = previous.payment_date
    except sender.DoesNotExist:
        instance._previous_status = None
        instance._previous_payment_date = None


@receiver(post_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, created, **kwargs):
    """
    Handle logic when a transaction status changes.
    
    When a transaction is marked as 'paid':
    - Log the event
    - Could trigger notifications or other side effects
    
    Note: The actual balance calculation is done dynamically via the
    Account.current_balance property, so no balance update is needed here.
    """
    if created:
        logger.info(
            "Transaction #%s created: %s %s (%s)",
            instance.id,
            instance.transaction_type,
            instance.gross_amount,
            instance.status
        )
        return
    
    prev_status = getattr(instance, '_previous_status', None)
    
    # Status changed
    if prev_status and prev_status != instance.status:
        logger.info(
            "Transaction #%s status changed: %s → %s",
            instance.id,
            prev_status,
            instance.status
        )
        
        # Transaction marked as paid
        if instance.status == 'paid' and prev_status != 'paid':
            _handle_transaction_paid(instance)
        
        # Transaction unmarked as paid
        elif prev_status == 'paid' and instance.status != 'paid':
            _handle_transaction_unpaid(instance)


def _handle_transaction_paid(transaction):
    """
    Handle side effects when a transaction is marked as paid.
    
    Could be extended to:
    - Send notifications
    - Update related records
    - Trigger reconciliation workflows
    """
    logger.info(
        "Transaction #%s marked as paid on %s",
        transaction.id,
        transaction.payment_date
    )
    
    # Future: Add notification logic here if needed
    # from base_modules.mailer.services import send_templated_email
    # send_templated_email(...)


def _handle_transaction_unpaid(transaction):
    """
    Handle side effects when a transaction is unmarked as paid.
    """
    logger.info(
        "Transaction #%s status reverted from paid to %s",
        transaction.id,
        transaction.status
    )
