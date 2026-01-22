from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from plugins.finance_manager_core.models import Category, Transaction
from plugins.finance_manager_accounts.models import Account


FREQUENCY_CHOICES = (
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('biweekly', 'Bi-weekly'),
    ('monthly', 'Monthly'),
    ('bimonthly', 'Bi-monthly'),
    ('quarterly', 'Quarterly'),
    ('semiannual', 'Semi-annual'),
    ('annual', 'Annual'),
)

PERIOD_CHOICES = (
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('semiannual', 'Semi-annual'),
    ('annual', 'Annual'),
)

TAX_APPLICABLE_CHOICES = (
    ('income', 'Income Only'),
    ('expense', 'Expenses Only'),
    ('all', 'All Transactions'),
    ('category', 'Specific Categories'),
)


class Budget(models.Model):
    """
    Represents a budget target for a specific category and period.
    Used for tracking spending/earning goals and generating alerts.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name="Category"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='budgets',
        blank=True,
        null=True,
        verbose_name="Account",
        help_text="Leave empty to apply budget across all accounts"
    )
    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Target Value",
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Budget limit or target amount"
    )
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        default='monthly',
        verbose_name="Period"
    )
    alert_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        verbose_name="Alert Threshold (%)",
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text="Percentage of budget at which to trigger an alert"
    )
    start_date = models.DateField(
        verbose_name="Start Date",
        help_text="When this budget becomes active"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="End Date",
        help_text="Leave empty for ongoing budget"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        ordering = ['-start_date', 'category__name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.target_value} ({self.get_period_display()})"

    def get_current_usage(self):
        """
        Calculate current spending/earning for this budget period.
        Returns a tuple of (amount, percentage).
        """
        from django.utils import timezone
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        today = timezone.now().date()
        
        # Determine the current period bounds
        if self.period == 'monthly':
            period_start = date(today.year, today.month, 1)
            period_end = period_start + relativedelta(months=1) - relativedelta(days=1)
        elif self.period == 'quarterly':
            quarter = (today.month - 1) // 3
            period_start = date(today.year, quarter * 3 + 1, 1)
            period_end = period_start + relativedelta(months=3) - relativedelta(days=1)
        elif self.period == 'semiannual':
            half = 0 if today.month <= 6 else 6
            period_start = date(today.year, half + 1, 1)
            period_end = period_start + relativedelta(months=6) - relativedelta(days=1)
        else:  # annual
            period_start = date(today.year, 1, 1)
            period_end = date(today.year, 12, 31)
        
        # Build query
        qs = Transaction.objects.filter(
            category=self.category,
            competence_date__gte=max(period_start, self.start_date),
            competence_date__lte=period_end,
            is_hypothetical=False,
            status__in=['pending', 'paid', 'scheduled']
        )
        
        if self.account:
            qs = qs.filter(account=self.account)
        
        if self.end_date:
            qs = qs.filter(competence_date__lte=self.end_date)
        
        from django.db.models import Sum
        total = qs.aggregate(total=Sum('gross_amount'))['total'] or Decimal('0.00')
        
        percentage = (total / self.target_value * 100) if self.target_value else Decimal('0.00')
        
        return total, percentage.quantize(Decimal('0.01'))

    @property
    def is_over_budget(self):
        """Check if current usage exceeds the budget."""
        _, percentage = self.get_current_usage()
        return percentage > 100

    @property
    def is_near_limit(self):
        """Check if current usage is near the alert threshold."""
        _, percentage = self.get_current_usage()
        return percentage >= self.alert_threshold


class RecurrenceRule(models.Model):
    """
    Defines a rule for generating recurring transactions.
    Links to a template transaction that will be duplicated.
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Rule Name"
    )
    template_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        related_name='recurrence_template',
        blank=True,
        null=True,
        verbose_name="Template Transaction",
        help_text="The transaction to use as a template for recurring copies"
    )
    # Alternatively, store the template data directly
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='recurrence_rules',
        verbose_name="Account"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='recurrence_rules',
        verbose_name="Category"
    )
    description = models.CharField(
        max_length=500,
        verbose_name="Description"
    )
    gross_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Gross Amount",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    vat_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="VAT Percentage"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=(('income', 'Income'), ('expense', 'Expense')),
        verbose_name="Transaction Type"
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='monthly',
        verbose_name="Frequency"
    )
    day_of_month = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Day of Month",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="For monthly/quarterly/annual: which day of the month"
    )
    day_of_week = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Day of Week",
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="For weekly: 0=Monday, 6=Sunday"
    )
    start_date = models.DateField(
        verbose_name="Start Date"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="End Date",
        help_text="Leave empty for indefinite recurrence"
    )
    last_generated_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Last Generated Date",
        help_text="Date of the last automatically generated transaction"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    generate_as_hypothetical = models.BooleanField(
        default=False,
        verbose_name="Generate as Hypothetical",
        help_text="Create future transactions as hypothetical for forecasting"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Recurrence Rule"
        verbose_name_plural = "Recurrence Rules"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'start_date']),
            models.Index(fields=['frequency']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

    def get_next_occurrence_date(self, from_date=None):
        """Calculate the next occurrence date based on frequency."""
        from django.utils import timezone
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        if from_date is None:
            from_date = self.last_generated_date or self.start_date
        
        if self.end_date and from_date >= self.end_date:
            return None
        
        if self.frequency == 'daily':
            next_date = from_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            next_date = from_date + timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            next_date = from_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            next_date = from_date + relativedelta(months=1)
            if self.day_of_month:
                try:
                    next_date = next_date.replace(day=self.day_of_month)
                except ValueError:
                    # Handle months with fewer days
                    next_date = next_date + relativedelta(months=1, day=1) - timedelta(days=1)
        elif self.frequency == 'bimonthly':
            next_date = from_date + relativedelta(months=2)
        elif self.frequency == 'quarterly':
            next_date = from_date + relativedelta(months=3)
        elif self.frequency == 'semiannual':
            next_date = from_date + relativedelta(months=6)
        elif self.frequency == 'annual':
            next_date = from_date + relativedelta(years=1)
        else:
            next_date = from_date + relativedelta(months=1)
        
        if self.end_date and next_date > self.end_date:
            return None
        
        return next_date

    def generate_transaction(self, for_date=None):
        """Generate a transaction based on this rule."""
        from django.utils import timezone
        
        if for_date is None:
            for_date = timezone.now().date()
        
        transaction = Transaction.objects.create(
            account=self.account,
            category=self.category,
            description=self.description,
            gross_amount=self.gross_amount,
            vat_percentage=self.vat_percentage,
            competence_date=for_date,
            transaction_type=self.transaction_type,
            status='pending',
            is_hypothetical=self.generate_as_hypothetical,
            data_source='recurring',
            recurring_rule=self
        )
        
        self.last_generated_date = for_date
        self.save(update_fields=['last_generated_date', 'updated_at'])
        
        return transaction


class TaxConfig(models.Model):
    """
    Configuration for tax rates and rules.
    Used for calculating tax provisions and obligations.
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Tax Name"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Tax Rate (%)",
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    applicable_to = models.CharField(
        max_length=20,
        choices=TAX_APPLICABLE_CHOICES,
        default='income',
        verbose_name="Applicable To"
    )
    applicable_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='tax_configs',
        verbose_name="Applicable Categories",
        help_text="Only used when 'Applicable To' is set to 'Specific Categories'"
    )
    threshold_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Threshold Amount",
        help_text="Minimum amount before this tax applies"
    )
    is_progressive = models.BooleanField(
        default=False,
        verbose_name="Progressive Tax",
        help_text="Tax rate applies only to amount above threshold"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    valid_from = models.DateField(
        verbose_name="Valid From"
    )
    valid_until = models.DateField(
        blank=True,
        null=True,
        verbose_name="Valid Until",
        help_text="Leave empty if currently valid"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tax Configuration"
        verbose_name_plural = "Tax Configurations"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'valid_from']),
            models.Index(fields=['applicable_to']),
        ]

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

    def calculate_tax(self, amount):
        """
        Calculate tax for a given amount.
        
        Args:
            amount: The gross amount to calculate tax on
            
        Returns:
            The calculated tax amount
        """
        if self.threshold_amount and amount <= self.threshold_amount:
            return Decimal('0.00')
        
        taxable_amount = amount
        if self.is_progressive and self.threshold_amount:
            taxable_amount = amount - self.threshold_amount
        
        return (taxable_amount * self.percentage / 100).quantize(Decimal('0.01'))
