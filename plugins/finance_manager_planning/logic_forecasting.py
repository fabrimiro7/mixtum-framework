"""
Cashflow forecasting logic for finance_manager_planning.

Provides:
- Short-term forecasting (3, 6, 12 months)
- Scenario-based projections
- Trend analysis
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta

from django.db.models import Sum, Q, Case, When, F, DecimalField
from django.db.models.functions import TruncMonth
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class ForecastPeriod:
    """Represents a single period in the forecast."""
    period_start: date
    period_end: date
    period_label: str
    projected_income: Decimal
    projected_expenses: Decimal
    net_cashflow: Decimal
    cumulative_balance: Decimal
    hypothetical_income: Decimal = Decimal('0.00')
    hypothetical_expenses: Decimal = Decimal('0.00')


@dataclass
class ForecastResult:
    """Complete forecast result with multiple periods."""
    start_date: date
    end_date: date
    months: int
    starting_balance: Decimal
    ending_balance: Decimal
    total_projected_income: Decimal
    total_projected_expenses: Decimal
    net_change: Decimal
    periods: List[ForecastPeriod]
    warnings: List[str]


class CashflowForecaster:
    """
    Engine for generating cashflow forecasts.
    
    Combines:
    - Historical transaction patterns
    - Recurring transaction rules
    - Hypothetical/planned transactions
    - Budget constraints
    """

    def __init__(self, account_ids: Optional[List[int]] = None):
        """
        Initialize the forecaster.
        
        Args:
            account_ids: List of account IDs to include. None = all accounts.
        """
        self.account_ids = account_ids

    def forecast(
        self,
        months: int = 3,
        start_date: Optional[date] = None,
        include_hypothetical: bool = True,
        include_recurring: bool = True,
        use_historical_averages: bool = True,
        historical_months: int = 6
    ) -> ForecastResult:
        """
        Generate a cashflow forecast for the specified period.
        
        Args:
            months: Number of months to forecast (3, 6, or 12 recommended)
            start_date: Start date for forecast (default: next month)
            include_hypothetical: Include hypothetical transactions
            include_recurring: Project recurring transactions
            use_historical_averages: Fill gaps with historical averages
            historical_months: Months of history to use for averages
            
        Returns:
            ForecastResult with period-by-period projections
        """
        from plugins.finance_manager_core.models import Transaction
        from plugins.finance_manager_accounts.models import Account
        from .models import RecurrenceRule
        
        today = timezone.now().date()
        
        if start_date is None:
            start_date = today.replace(day=1) + relativedelta(months=1)
        
        end_date = start_date + relativedelta(months=months) - timedelta(days=1)
        
        warnings = []
        
        # Calculate starting balance from all relevant accounts
        starting_balance = self._calculate_starting_balance()
        
        # Get historical averages if needed
        historical_income_avg = Decimal('0.00')
        historical_expense_avg = Decimal('0.00')
        
        if use_historical_averages:
            historical_income_avg, historical_expense_avg = self._calculate_historical_averages(
                historical_months
            )
        
        # Generate period-by-period forecast
        periods = []
        cumulative_balance = starting_balance
        total_income = Decimal('0.00')
        total_expenses = Decimal('0.00')
        
        current = start_date
        while current < end_date:
            period_start = current
            period_end = (current + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
            if period_end > end_date:
                period_end = end_date
            
            period_label = current.strftime('%Y-%m')
            
            # Get scheduled/pending transactions for this period
            income, expenses = self._get_scheduled_transactions(period_start, period_end)
            
            # Add hypothetical transactions
            hypo_income = Decimal('0.00')
            hypo_expenses = Decimal('0.00')
            if include_hypothetical:
                hypo_income, hypo_expenses = self._get_hypothetical_transactions(
                    period_start, period_end
                )
            
            # Project recurring transactions
            recurring_income = Decimal('0.00')
            recurring_expenses = Decimal('0.00')
            if include_recurring:
                recurring_income, recurring_expenses = self._project_recurring_transactions(
                    period_start, period_end
                )
            
            # Combine projections
            projected_income = income + hypo_income + recurring_income
            projected_expenses = expenses + hypo_expenses + recurring_expenses
            
            # Fill with historical averages if no data
            if use_historical_averages:
                if projected_income == 0 and historical_income_avg > 0:
                    projected_income = historical_income_avg
                    warnings.append(
                        f"Using historical average for income in {period_label}"
                    )
                if projected_expenses == 0 and historical_expense_avg > 0:
                    projected_expenses = historical_expense_avg
                    warnings.append(
                        f"Using historical average for expenses in {period_label}"
                    )
            
            net_cashflow = projected_income - projected_expenses
            cumulative_balance += net_cashflow
            total_income += projected_income
            total_expenses += projected_expenses
            
            periods.append(ForecastPeriod(
                period_start=period_start,
                period_end=period_end,
                period_label=period_label,
                projected_income=projected_income,
                projected_expenses=projected_expenses,
                net_cashflow=net_cashflow,
                cumulative_balance=cumulative_balance,
                hypothetical_income=hypo_income,
                hypothetical_expenses=hypo_expenses
            ))
            
            current = current + relativedelta(months=1)
        
        # Check for negative balance warnings
        min_balance = min(p.cumulative_balance for p in periods) if periods else starting_balance
        if min_balance < 0:
            warnings.append(
                f"Warning: Projected balance goes negative (min: {min_balance:.2f})"
            )
        
        return ForecastResult(
            start_date=start_date,
            end_date=end_date,
            months=months,
            starting_balance=starting_balance,
            ending_balance=cumulative_balance,
            total_projected_income=total_income,
            total_projected_expenses=total_expenses,
            net_change=total_income - total_expenses,
            periods=periods,
            warnings=warnings
        )

    def _calculate_starting_balance(self) -> Decimal:
        """Calculate the current total balance across relevant accounts."""
        from plugins.finance_manager_accounts.models import Account
        
        accounts = Account.objects.filter(
            is_active=True,
            include_in_totals=True
        )
        
        if self.account_ids:
            accounts = accounts.filter(id__in=self.account_ids)
        
        total = Decimal('0.00')
        for account in accounts:
            try:
                total += account.current_balance
            except Exception:
                pass
        
        return total

    def _calculate_historical_averages(self, months: int) -> Tuple[Decimal, Decimal]:
        """Calculate average monthly income and expenses from historical data."""
        from plugins.finance_manager_core.models import Transaction
        
        today = timezone.now().date()
        start = today - relativedelta(months=months)
        
        qs = Transaction.objects.filter(
            competence_date__gte=start,
            competence_date__lt=today.replace(day=1),
            is_hypothetical=False,
            status__in=['paid', 'pending']
        )
        
        if self.account_ids:
            qs = qs.filter(account_id__in=self.account_ids)
        
        result = qs.aggregate(
            total_income=Sum(
                Case(
                    When(transaction_type='income', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            ),
            total_expenses=Sum(
                Case(
                    When(transaction_type='expense', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            )
        )
        
        total_income = result['total_income'] or Decimal('0.00')
        total_expenses = result['total_expenses'] or Decimal('0.00')
        
        if months > 0:
            return (
                (total_income / months).quantize(Decimal('0.01')),
                (total_expenses / months).quantize(Decimal('0.01'))
            )
        
        return Decimal('0.00'), Decimal('0.00')

    def _get_scheduled_transactions(
        self,
        start: date,
        end: date
    ) -> Tuple[Decimal, Decimal]:
        """Get scheduled/pending transactions for a period."""
        from plugins.finance_manager_core.models import Transaction
        
        qs = Transaction.objects.filter(
            competence_date__gte=start,
            competence_date__lte=end,
            is_hypothetical=False,
            status__in=['pending', 'scheduled']
        )
        
        if self.account_ids:
            qs = qs.filter(account_id__in=self.account_ids)
        
        result = qs.aggregate(
            income=Sum(
                Case(
                    When(transaction_type='income', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            ),
            expenses=Sum(
                Case(
                    When(transaction_type='expense', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            )
        )
        
        return (
            result['income'] or Decimal('0.00'),
            result['expenses'] or Decimal('0.00')
        )

    def _get_hypothetical_transactions(
        self,
        start: date,
        end: date
    ) -> Tuple[Decimal, Decimal]:
        """Get hypothetical transactions for forecasting."""
        from plugins.finance_manager_core.models import Transaction
        
        qs = Transaction.objects.filter(
            competence_date__gte=start,
            competence_date__lte=end,
            is_hypothetical=True,
            status__in=['pending', 'scheduled']
        )
        
        if self.account_ids:
            qs = qs.filter(account_id__in=self.account_ids)
        
        result = qs.aggregate(
            income=Sum(
                Case(
                    When(transaction_type='income', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            ),
            expenses=Sum(
                Case(
                    When(transaction_type='expense', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            )
        )
        
        return (
            result['income'] or Decimal('0.00'),
            result['expenses'] or Decimal('0.00')
        )

    def _project_recurring_transactions(
        self,
        start: date,
        end: date
    ) -> Tuple[Decimal, Decimal]:
        """
        Project recurring transactions that haven't been generated yet.
        
        This estimates what recurring rules would generate if they run.
        """
        from .models import RecurrenceRule
        
        qs = RecurrenceRule.objects.filter(
            is_active=True,
            start_date__lte=end
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=start)
        )
        
        if self.account_ids:
            qs = qs.filter(account_id__in=self.account_ids)
        
        income = Decimal('0.00')
        expenses = Decimal('0.00')
        
        for rule in qs:
            # Count occurrences in the period
            occurrences = self._count_occurrences(rule, start, end)
            total = rule.gross_amount * occurrences
            
            if rule.transaction_type == 'income':
                income += total
            else:
                expenses += total
        
        return income, expenses

    def _count_occurrences(self, rule, start: date, end: date) -> int:
        """Count how many times a recurring rule would trigger in a period."""
        count = 0
        current = rule.last_generated_date or rule.start_date
        
        # Start from before the period to catch the first occurrence
        if current >= start:
            current = start - timedelta(days=1)
        
        while True:
            next_date = rule.get_next_occurrence_date(current)
            
            if next_date is None or next_date > end:
                break
            
            if next_date >= start:
                count += 1
            
            current = next_date
        
        return count


def generate_forecast(
    months: int = 3,
    account_ids: Optional[List[int]] = None,
    **kwargs
) -> Dict:
    """
    Convenience function to generate a forecast.
    
    Args:
        months: Number of months to forecast
        account_ids: Optional list of account IDs to include
        **kwargs: Additional arguments passed to CashflowForecaster.forecast()
        
    Returns:
        Dict representation of ForecastResult
    """
    forecaster = CashflowForecaster(account_ids=account_ids)
    result = forecaster.forecast(months=months, **kwargs)
    
    return {
        'start_date': result.start_date.isoformat(),
        'end_date': result.end_date.isoformat(),
        'months': result.months,
        'starting_balance': float(result.starting_balance),
        'ending_balance': float(result.ending_balance),
        'total_projected_income': float(result.total_projected_income),
        'total_projected_expenses': float(result.total_projected_expenses),
        'net_change': float(result.net_change),
        'periods': [
            {
                'period_start': p.period_start.isoformat(),
                'period_end': p.period_end.isoformat(),
                'period_label': p.period_label,
                'projected_income': float(p.projected_income),
                'projected_expenses': float(p.projected_expenses),
                'net_cashflow': float(p.net_cashflow),
                'cumulative_balance': float(p.cumulative_balance),
                'hypothetical_income': float(p.hypothetical_income),
                'hypothetical_expenses': float(p.hypothetical_expenses)
            }
            for p in result.periods
        ],
        'warnings': result.warnings
    }


def forecast_3_months(account_ids: Optional[List[int]] = None) -> Dict:
    """Shortcut for 3-month forecast."""
    return generate_forecast(months=3, account_ids=account_ids)


def forecast_6_months(account_ids: Optional[List[int]] = None) -> Dict:
    """Shortcut for 6-month forecast."""
    return generate_forecast(months=6, account_ids=account_ids)


def forecast_12_months(account_ids: Optional[List[int]] = None) -> Dict:
    """Shortcut for 12-month (annual) forecast."""
    return generate_forecast(months=12, account_ids=account_ids)
