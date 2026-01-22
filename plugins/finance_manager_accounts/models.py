from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal


CURRENCY_CHOICES = (
    ('EUR', 'Euro (€)'),
    ('USD', 'US Dollar ($)'),
    ('GBP', 'British Pound (£)'),
    ('CHF', 'Swiss Franc (CHF)'),
    ('JPY', 'Japanese Yen (¥)'),
)


class Bank(models.Model):
    """
    Represents a banking institution.
    Stores basic information like name and identification codes.
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Bank Name"
    )
    abi_code = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name="ABI Code",
        help_text="Italian bank ABI code (5 digits)",
        validators=[RegexValidator(r'^\d{5}$', 'ABI code must be exactly 5 digits')]
    )
    swift_code = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name="SWIFT/BIC Code",
        help_text="International SWIFT/BIC code (8-11 characters)",
        validators=[RegexValidator(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', 'Invalid SWIFT/BIC format')]
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name="Country Code",
        help_text="ISO 3166-1 alpha-2 country code"
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        ordering = ['name']

    def __str__(self):
        if self.swift_code:
            return f"{self.name} ({self.swift_code})"
        return self.name


class Account(models.Model):
    """
    Represents a bank account or cash reserve.
    Tracks the initial balance and links to a specific bank.
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Account Name"
    )
    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name='accounts',
        blank=True,
        null=True,
        verbose_name="Bank",
        help_text="Leave empty for cash/physical reserves"
    )
    iban = models.CharField(
        max_length=34,
        blank=True,
        null=True,
        verbose_name="IBAN",
        help_text="International Bank Account Number",
        validators=[RegexValidator(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$', 'Invalid IBAN format')]
    )
    initial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Initial Balance",
        help_text="Starting balance when the account was added to the system"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR',
        verbose_name="Currency"
    )
    account_type = models.CharField(
        max_length=50,
        choices=(
            ('checking', 'Checking Account'),
            ('savings', 'Savings Account'),
            ('business', 'Business Account'),
            ('cash', 'Physical Cash'),
            ('investment', 'Investment Account'),
            ('credit_card', 'Credit Card'),
            ('other', 'Other'),
        ),
        default='checking',
        verbose_name="Account Type"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    include_in_totals = models.BooleanField(
        default=True,
        verbose_name="Include in Totals",
        help_text="Include this account when calculating aggregate balances"
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Color",
        help_text="Hex color code for UI display (e.g., #3498db)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'include_in_totals']),
        ]

    def __str__(self):
        if self.bank:
            return f"{self.name} ({self.bank.name})"
        return self.name

    @property
    def current_balance(self):
        """
        Calculate the current balance based on initial balance and all transactions.
        This property aggregates all related transactions from finance_manager_core.
        """
        from plugins.finance_manager_core.models import Transaction
        from django.db.models import Sum, Case, When, F, DecimalField
        from decimal import Decimal

        transactions = Transaction.objects.filter(
            account=self,
            is_hypothetical=False,
            status='paid'
        ).aggregate(
            total_income=Sum(
                Case(
                    When(transaction_type='income', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            ),
            total_expense=Sum(
                Case(
                    When(transaction_type='expense', then=F('gross_amount')),
                    default=Decimal('0.00'),
                    output_field=DecimalField()
                )
            )
        )

        total_income = transactions['total_income'] or Decimal('0.00')
        total_expense = transactions['total_expense'] or Decimal('0.00')

        return self.initial_balance + total_income - total_expense
