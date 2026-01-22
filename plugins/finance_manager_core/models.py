from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from plugins.finance_manager_accounts.models import Account
from .managers import TransactionManager, CategoryManager


TRANSACTION_TYPE_CHOICES = (
    ('income', 'Income'),
    ('expense', 'Expense'),
)

TRANSACTION_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('scheduled', 'Scheduled'),
    ('paid', 'Paid'),
    ('cancelled', 'Cancelled'),
)

DATA_SOURCE_CHOICES = (
    ('manual', 'Manual Entry'),
    ('import_csv', 'CSV Import'),
    ('import_excel', 'Excel Import'),
    ('import_bank', 'Bank Statement Import'),
    ('recurring', 'Recurring Transaction'),
    ('api', 'API Integration'),
)


class Category(models.Model):
    """
    Represents a transaction category with support for hierarchical subcategories.
    Categories can be nested using the parent field.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Category Name"
    )
    color = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name="Color",
        help_text="Hex color code for UI display (e.g., #3498db)"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Icon",
        help_text="Icon identifier (e.g., FontAwesome class or Material icon name)"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        blank=True,
        null=True,
        verbose_name="Parent Category",
        help_text="Leave empty for top-level categories"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Default Transaction Type",
        help_text="Restrict this category to a specific transaction type"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Sort Order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = CategoryManager()

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def full_path(self):
        """Return the full category path including all ancestors."""
        if self.parent:
            return f"{self.parent.full_path} → {self.name}"
        return self.name

    @property
    def depth(self):
        """Return the depth level of this category in the hierarchy."""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level


class Transaction(models.Model):
    """
    Represents a financial transaction (income or expense).
    Core entity for the cashflow management system.
    """
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="Account"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions',
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
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Positive value; transaction type determines direction"
    )
    vat_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="VAT Percentage",
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="VAT/Tax percentage (0-100)"
    )
    competence_date = models.DateField(
        verbose_name="Competence Date",
        help_text="The date the transaction is attributed to (accounting date)"
    )
    payment_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Payment Date",
        help_text="The actual date of payment (leave empty if not yet paid)"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name="Type"
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    is_hypothetical = models.BooleanField(
        default=False,
        verbose_name="Hypothetical",
        help_text="Mark as hypothetical for cashflow forecasting scenarios"
    )
    data_source = models.CharField(
        max_length=20,
        choices=DATA_SOURCE_CHOICES,
        default='manual',
        verbose_name="Data Source"
    )
    external_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="External Reference",
        help_text="Reference ID from external system (bank statement, invoice, etc.)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    # For recurring transactions
    recurring_rule = models.ForeignKey(
        'finance_manager_planning.RecurrenceRule',
        on_delete=models.SET_NULL,
        related_name='generated_transactions',
        blank=True,
        null=True,
        verbose_name="Recurrence Rule"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = TransactionManager()

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-competence_date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['category', 'transaction_type']),
            models.Index(fields=['competence_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['is_hypothetical', 'status']),
        ]

    def __str__(self):
        sign = '+' if self.transaction_type == 'income' else '-'
        return f"{sign}{self.gross_amount} | {self.description[:50]}"

    @property
    def net_amount(self):
        """Calculate net amount after VAT."""
        if self.vat_percentage == 0:
            return self.gross_amount
        vat_multiplier = 1 + (self.vat_percentage / 100)
        return (self.gross_amount / vat_multiplier).quantize(Decimal('0.01'))

    @property
    def vat_amount(self):
        """Calculate the VAT portion of the gross amount."""
        return (self.gross_amount - self.net_amount).quantize(Decimal('0.01'))

    @property
    def signed_amount(self):
        """Return the amount with appropriate sign (negative for expenses)."""
        if self.transaction_type == 'expense':
            return -self.gross_amount
        return self.gross_amount

    def mark_as_paid(self, payment_date=None):
        """Mark the transaction as paid."""
        from django.utils import timezone
        self.status = 'paid'
        self.payment_date = payment_date or timezone.now().date()
        self.save(update_fields=['status', 'payment_date', 'updated_at'])
