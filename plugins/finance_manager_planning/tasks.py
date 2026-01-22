"""
Celery tasks for finance_manager_planning.

Handles:
- Automatic generation of recurring transactions
- Budget alert notifications
- Periodic financial summaries
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import RecurrenceRule, Budget

logger = logging.getLogger(__name__)


@shared_task
def generate_recurring_transactions(
    lookahead_days: int = 7,
    generate_for_today: bool = True
) -> dict:
    """
    Generate recurring transactions based on active recurrence rules.
    
    This task should be scheduled to run daily (e.g., at midnight or early morning).
    
    Args:
        lookahead_days: Number of days ahead to generate transactions for.
                       Set to 0 to only generate for past due transactions.
        generate_for_today: Whether to include today's date in generation.
    
    Returns:
        Dict with generation statistics
    """
    today = timezone.now().date()
    end_date = today + timedelta(days=lookahead_days)
    
    if not generate_for_today:
        today = today + timedelta(days=1)
    
    stats = {
        'rules_processed': 0,
        'transactions_created': 0,
        'errors': []
    }
    
    active_rules = RecurrenceRule.objects.filter(
        is_active=True,
        start_date__lte=end_date
    ).select_related('account', 'category')
    
    for rule in active_rules:
        stats['rules_processed'] += 1
        
        try:
            transactions_created = _process_recurrence_rule(rule, today, end_date)
            stats['transactions_created'] += transactions_created
        except Exception as e:
            logger.exception("Error processing recurrence rule #%s", rule.id)
            stats['errors'].append({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'error': str(e)
            })
    
    logger.info(
        "Recurring transactions generated: %d transactions from %d rules",
        stats['transactions_created'],
        stats['rules_processed']
    )
    
    return stats


def _process_recurrence_rule(rule: RecurrenceRule, start: date, end: date) -> int:
    """
    Process a single recurrence rule and generate due transactions.
    
    Returns the number of transactions created.
    """
    if rule.end_date and rule.end_date < start:
        return 0
    
    created_count = 0
    current_date = rule.last_generated_date or rule.start_date
    
    # If we haven't generated yet and start_date is before our window
    if current_date < start:
        current_date = start - timedelta(days=1)
    
    # Generate transactions for each occurrence in the window
    while True:
        next_date = rule.get_next_occurrence_date(current_date)
        
        if next_date is None:
            break
        
        if next_date > end:
            break
        
        if next_date >= start:
            with transaction.atomic():
                tx = rule.generate_transaction(for_date=next_date)
                logger.debug(
                    "Generated transaction #%s for rule '%s' on %s",
                    tx.id, rule.name, next_date
                )
                created_count += 1
        
        current_date = next_date
    
    return created_count


@shared_task
def check_budget_alerts() -> dict:
    """
    Check all active budgets and generate alerts for those near or over limit.
    
    This task should be scheduled to run daily.
    
    Returns:
        Dict with alert statistics
    """
    today = timezone.now().date()
    
    stats = {
        'budgets_checked': 0,
        'near_limit': [],
        'over_budget': []
    }
    
    active_budgets = Budget.objects.filter(
        is_active=True,
        start_date__lte=today
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    ).select_related('category', 'account')
    
    for budget in active_budgets:
        stats['budgets_checked'] += 1
        
        try:
            current_amount, percentage = budget.get_current_usage()
            
            alert_data = {
                'budget_id': budget.id,
                'category': budget.category.name,
                'target': float(budget.target_value),
                'current': float(current_amount),
                'percentage': float(percentage),
                'period': budget.period
            }
            
            if percentage > 100:
                stats['over_budget'].append(alert_data)
                _send_budget_alert(budget, 'over_budget', current_amount, percentage)
            elif percentage >= budget.alert_threshold:
                stats['near_limit'].append(alert_data)
                _send_budget_alert(budget, 'near_limit', current_amount, percentage)
                
        except Exception as e:
            logger.exception("Error checking budget #%s", budget.id)
    
    logger.info(
        "Budget check complete: %d checked, %d near limit, %d over budget",
        stats['budgets_checked'],
        len(stats['near_limit']),
        len(stats['over_budget'])
    )
    
    return stats


def _send_budget_alert(budget: Budget, alert_type: str, amount: Decimal, percentage: Decimal):
    """
    Send a budget alert notification.
    
    This is a placeholder that can be extended to send emails,
    push notifications, or other alerts.
    """
    # Placeholder for notification logic
    # Could integrate with base_modules.mailer.services
    logger.warning(
        "Budget alert [%s]: %s - %.2f%% (%.2f / %.2f)",
        alert_type,
        budget.category.name,
        percentage,
        amount,
        budget.target_value
    )
    
    # Example integration with mailer (uncomment when needed):
    # from base_modules.mailer.services import send_templated_email
    # send_templated_email(
    #     template_slug=f'budget_{alert_type}',
    #     to=['admin@example.com'],
    #     context={
    #         'budget': budget,
    #         'amount': amount,
    #         'percentage': percentage,
    #         'alert_type': alert_type
    #     }
    # )


@shared_task
def generate_monthly_forecast(months_ahead: int = 3) -> dict:
    """
    Generate forecast transactions for the specified number of months.
    
    This task generates hypothetical transactions based on recurrence rules
    for cash flow forecasting purposes.
    
    Should be run at the beginning of each month.
    
    Args:
        months_ahead: Number of months to forecast (default: 3)
    
    Returns:
        Dict with forecast statistics
    """
    from dateutil.relativedelta import relativedelta
    
    today = timezone.now().date()
    # Start from next month
    start = (today.replace(day=1) + relativedelta(months=1))
    end = start + relativedelta(months=months_ahead) - timedelta(days=1)
    
    stats = {
        'period': {
            'start': start.isoformat(),
            'end': end.isoformat(),
            'months': months_ahead
        },
        'rules_processed': 0,
        'transactions_created': 0,
        'errors': []
    }
    
    # Get rules that generate hypothetical transactions
    forecast_rules = RecurrenceRule.objects.filter(
        is_active=True,
        generate_as_hypothetical=True,
        start_date__lte=end
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=start)
    ).select_related('account', 'category')
    
    for rule in forecast_rules:
        stats['rules_processed'] += 1
        
        try:
            count = _process_recurrence_rule(rule, start, end)
            stats['transactions_created'] += count
        except Exception as e:
            logger.exception("Error generating forecast for rule #%s", rule.id)
            stats['errors'].append({
                'rule_id': rule.id,
                'error': str(e)
            })
    
    logger.info(
        "Monthly forecast generated: %d transactions for %d months ahead",
        stats['transactions_created'],
        months_ahead
    )
    
    return stats


# Import models at module level for Celery task serialization
from django.db import models
