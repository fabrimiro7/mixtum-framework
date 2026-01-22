from django.db import models
from django.db.models import Sum, Q, F, Case, When, DecimalField
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal


class TransactionQuerySet(models.QuerySet):
    """Custom QuerySet for Transaction model with common filters."""

    def income(self):
        """Filter to income transactions only."""
        return self.filter(transaction_type='income')

    def expense(self):
        """Filter to expense transactions only (alias for expenses)."""
        return self.filter(transaction_type='expense')

    def expenses(self):
        """Filter to expense transactions only."""
        return self.filter(transaction_type='expense')

    def paid(self):
        """Filter to paid transactions only."""
        return self.filter(status='paid')

    def pending(self):
        """Filter to pending transactions only."""
        return self.filter(status='pending')

    def scheduled(self):
        """Filter to scheduled transactions only."""
        return self.filter(status='scheduled')

    def not_cancelled(self):
        """Exclude cancelled transactions."""
        return self.exclude(status='cancelled')

    def real(self):
        """Filter to non-hypothetical transactions."""
        return self.filter(is_hypothetical=False)

    def hypothetical(self):
        """Filter to hypothetical transactions only."""
        return self.filter(is_hypothetical=True)

    def for_account(self, account_id):
        """Filter transactions for a specific account."""
        return self.filter(account_id=account_id)

    def for_category(self, category_id, include_subcategories=True):
        """
        Filter transactions for a specific category.
        Optionally includes subcategories.
        """
        if include_subcategories:
            from plugins.finance_manager_core.models import Category
            category_ids = [category_id]
            # Get all subcategory IDs recursively
            subcats = Category.objects.filter(parent_id=category_id).values_list('id', flat=True)
            while subcats:
                category_ids.extend(subcats)
                subcats = Category.objects.filter(parent_id__in=subcats).values_list('id', flat=True)
            return self.filter(category_id__in=category_ids)
        return self.filter(category_id=category_id)

    def this_month(self):
        """Filter to transactions in the current month."""
        today = timezone.now().date()
        start = date(today.year, today.month, 1)
        end = start + relativedelta(months=1) - relativedelta(days=1)
        return self.filter(competence_date__gte=start, competence_date__lte=end)

    def this_year(self):
        """Filter to transactions in the current year."""
        today = timezone.now().date()
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        return self.filter(competence_date__gte=start, competence_date__lte=end)

    def last_n_months(self, n):
        """Filter to transactions in the last N months."""
        today = timezone.now().date()
        start = today - relativedelta(months=n)
        return self.filter(competence_date__gte=start, competence_date__lte=today)

    def in_date_range(self, start_date, end_date):
        """Filter transactions within a date range."""
        return self.filter(competence_date__gte=start_date, competence_date__lte=end_date)

    def overdue(self):
        """Filter to pending/scheduled transactions past their competence date."""
        today = timezone.now().date()
        return self.filter(
            status__in=['pending', 'scheduled'],
            competence_date__lt=today
        )

    def due_soon(self, days=7):
        """Filter to pending transactions due within the next N days."""
        today = timezone.now().date()
        end = today + relativedelta(days=days)
        return self.filter(
            status__in=['pending', 'scheduled'],
            competence_date__gte=today,
            competence_date__lte=end
        )

    def income_this_month(self):
        """Shortcut: income transactions for current month."""
        return self.income().this_month().real().not_cancelled()

    def expenses_this_month(self):
        """Shortcut: expense transactions for current month."""
        return self.expenses().this_month().real().not_cancelled()

    def overdue_expenses(self):
        """Shortcut: overdue expense transactions."""
        return self.expenses().overdue().real()

    def hypothetical_cashflow(self):
        """Shortcut: hypothetical transactions for forecasting."""
        return self.hypothetical().not_cancelled()

    # Aggregation methods
    def total_income(self):
        """Calculate total income amount."""
        result = self.income().aggregate(
            total=Sum('gross_amount')
        )
        return result['total'] or Decimal('0.00')

    def total_expenses(self):
        """Calculate total expense amount."""
        result = self.expenses().aggregate(
            total=Sum('gross_amount')
        )
        return result['total'] or Decimal('0.00')

    def net_cashflow(self):
        """Calculate net cashflow (income - expenses)."""
        result = self.aggregate(
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
        income = result['income'] or Decimal('0.00')
        expenses = result['expenses'] or Decimal('0.00')
        return income - expenses


class TransactionManager(models.Manager):
    """Manager that uses TransactionQuerySet."""

    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)

    def income(self):
        return self.get_queryset().income()

    def expense(self):
        return self.get_queryset().expense()

    def expenses(self):
        return self.get_queryset().expenses()

    def paid(self):
        return self.get_queryset().paid()

    def pending(self):
        return self.get_queryset().pending()

    def real(self):
        return self.get_queryset().real()

    def hypothetical(self):
        return self.get_queryset().hypothetical()

    def this_month(self):
        return self.get_queryset().this_month()

    def this_year(self):
        return self.get_queryset().this_year()

    def overdue(self):
        return self.get_queryset().overdue()

    def income_this_month(self):
        return self.get_queryset().income_this_month()

    def expenses_this_month(self):
        return self.get_queryset().expenses_this_month()


class CategoryQuerySet(models.QuerySet):
    """Custom QuerySet for Category model."""

    def active(self):
        """Filter to active categories only."""
        return self.filter(is_active=True)

    def top_level(self):
        """Filter to top-level categories only (no parent)."""
        return self.filter(parent__isnull=True)

    def income_categories(self):
        """Filter to categories designated for income."""
        return self.filter(Q(transaction_type='income') | Q(transaction_type__isnull=True))

    def expense_categories(self):
        """Filter to categories designated for expenses."""
        return self.filter(Q(transaction_type='expense') | Q(transaction_type__isnull=True))

    def with_transaction_count(self):
        """Annotate with transaction count."""
        from django.db.models import Count
        return self.annotate(transaction_count=Count('transactions'))


class CategoryManager(models.Manager):
    """Manager that uses CategoryQuerySet."""

    def get_queryset(self):
        return CategoryQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def top_level(self):
        return self.get_queryset().top_level()

    def income_categories(self):
        return self.get_queryset().income_categories()

    def expense_categories(self):
        return self.get_queryset().expense_categories()
