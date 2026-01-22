from rest_framework import serializers
from decimal import Decimal

from .models import Budget, RecurrenceRule, TaxConfig
from plugins.finance_manager_core.serializers import CategoryMinimalSerializer
from plugins.finance_manager_accounts.serializers import AccountMinimalSerializer


class BudgetSerializer(serializers.ModelSerializer):
    category = CategoryMinimalSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=lambda: __import__('plugins.finance_manager_core.models', fromlist=['Category']).Category.objects.filter(is_active=True),
        source='category',
        write_only=True
    )
    account = AccountMinimalSerializer(read_only=True)
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=lambda: __import__('plugins.finance_manager_accounts.models', fromlist=['Account']).Account.objects.filter(is_active=True),
        source='account',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Computed fields
    current_usage = serializers.SerializerMethodField()
    current_percentage = serializers.SerializerMethodField()
    is_over_budget = serializers.BooleanField(read_only=True)
    is_near_limit = serializers.BooleanField(read_only=True)
    
    # Display fields
    period_display = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'category_id', 'account', 'account_id',
            'target_value', 'period', 'period_display',
            'alert_threshold', 'start_date', 'end_date',
            'is_active', 'notes',
            'current_usage', 'current_percentage',
            'is_over_budget', 'is_near_limit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_current_usage(self, obj):
        amount, _ = obj.get_current_usage()
        return amount

    def get_current_percentage(self, obj):
        _, percentage = obj.get_current_usage()
        return percentage


class BudgetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating budgets."""
    
    class Meta:
        model = Budget
        fields = [
            'category', 'account', 'target_value', 'period',
            'alert_threshold', 'start_date', 'end_date',
            'is_active', 'notes'
        ]


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    account = AccountMinimalSerializer(read_only=True)
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=lambda: __import__('plugins.finance_manager_accounts.models', fromlist=['Account']).Account.objects.filter(is_active=True),
        source='account',
        write_only=True
    )
    category = CategoryMinimalSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=lambda: __import__('plugins.finance_manager_core.models', fromlist=['Category']).Category.objects.filter(is_active=True),
        source='category',
        write_only=True
    )
    
    # Display fields
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    next_occurrence = serializers.SerializerMethodField()
    generated_count = serializers.SerializerMethodField()

    class Meta:
        model = RecurrenceRule
        fields = [
            'id', 'name', 'template_transaction',
            'account', 'account_id', 'category', 'category_id',
            'description', 'gross_amount', 'vat_percentage',
            'transaction_type', 'transaction_type_display',
            'frequency', 'frequency_display',
            'day_of_month', 'day_of_week',
            'start_date', 'end_date', 'last_generated_date',
            'is_active', 'generate_as_hypothetical', 'notes',
            'next_occurrence', 'generated_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_generated_date', 'template_transaction']

    def get_next_occurrence(self, obj):
        next_date = obj.get_next_occurrence_date()
        return next_date.isoformat() if next_date else None

    def get_generated_count(self, obj):
        return obj.generated_transactions.count()


class RecurrenceRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recurrence rules."""
    
    class Meta:
        model = RecurrenceRule
        fields = [
            'name', 'account', 'category', 'description',
            'gross_amount', 'vat_percentage', 'transaction_type',
            'frequency', 'day_of_month', 'day_of_week',
            'start_date', 'end_date', 'is_active',
            'generate_as_hypothetical', 'notes'
        ]


class TaxConfigSerializer(serializers.ModelSerializer):
    applicable_categories = CategoryMinimalSerializer(many=True, read_only=True)
    applicable_category_ids = serializers.PrimaryKeyRelatedField(
        queryset=lambda: __import__('plugins.finance_manager_core.models', fromlist=['Category']).Category.objects.filter(is_active=True),
        source='applicable_categories',
        write_only=True,
        many=True,
        required=False
    )
    
    # Display fields
    applicable_to_display = serializers.CharField(source='get_applicable_to_display', read_only=True)

    class Meta:
        model = TaxConfig
        fields = [
            'id', 'name', 'percentage',
            'applicable_to', 'applicable_to_display',
            'applicable_categories', 'applicable_category_ids',
            'threshold_amount', 'is_progressive',
            'description', 'valid_from', 'valid_until',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaxConfigCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tax configurations."""
    
    class Meta:
        model = TaxConfig
        fields = [
            'name', 'percentage', 'applicable_to',
            'applicable_categories', 'threshold_amount',
            'is_progressive', 'description',
            'valid_from', 'valid_until', 'is_active'
        ]


class ForecastPeriodSerializer(serializers.Serializer):
    """Serializer for a single forecast period."""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_label = serializers.CharField()
    projected_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    projected_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_cashflow = serializers.DecimalField(max_digits=15, decimal_places=2)
    cumulative_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    hypothetical_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    hypothetical_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)


class ForecastResultSerializer(serializers.Serializer):
    """Serializer for complete forecast results."""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    months = serializers.IntegerField()
    starting_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    ending_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_projected_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_projected_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_change = serializers.DecimalField(max_digits=15, decimal_places=2)
    periods = ForecastPeriodSerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())


class ForecastRequestSerializer(serializers.Serializer):
    """Serializer for forecast request parameters."""
    months = serializers.IntegerField(default=3, min_value=1, max_value=24)
    account_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True
    )
    include_hypothetical = serializers.BooleanField(default=True)
    include_recurring = serializers.BooleanField(default=True)
    use_historical_averages = serializers.BooleanField(default=True)
    historical_months = serializers.IntegerField(default=6, min_value=1, max_value=24)
