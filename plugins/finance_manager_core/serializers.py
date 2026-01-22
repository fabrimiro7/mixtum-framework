from rest_framework import serializers
from decimal import Decimal

from .models import Category, Transaction
from plugins.finance_manager_accounts.serializers import AccountMinimalSerializer


class CategorySerializer(serializers.ModelSerializer):
    full_path = serializers.CharField(read_only=True)
    depth = serializers.IntegerField(read_only=True)
    subcategories_count = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'color', 'icon', 'parent', 'description',
            'transaction_type', 'is_active', 'sort_order',
            'full_path', 'depth', 'subcategories_count', 'transaction_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_subcategories_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()

    def get_transaction_count(self, obj):
        return obj.transactions.count()


class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested representations."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon']


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer for hierarchical category tree."""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon', 'transaction_type', 'children']

    def get_children(self, obj):
        children = obj.subcategories.filter(is_active=True).order_by('sort_order', 'name')
        return CategoryTreeSerializer(children, many=True).data


class TransactionSerializer(serializers.ModelSerializer):
    account = AccountMinimalSerializer(read_only=True)
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=lambda: __import__('plugins.finance_manager_accounts.models', fromlist=['Account']).Account.objects.all(),
        source='account',
        write_only=True
    )
    category = CategoryMinimalSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True
    )
    
    # Computed fields
    net_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    vat_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    signed_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    # Display fields
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    data_source_display = serializers.CharField(
        source='get_data_source_display',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_id', 'category', 'category_id',
            'description', 'gross_amount', 'net_amount', 'vat_amount', 'signed_amount',
            'vat_percentage', 'competence_date', 'payment_date',
            'transaction_type', 'transaction_type_display',
            'status', 'status_display',
            'is_hypothetical', 'data_source', 'data_source_display',
            'external_reference', 'notes', 'recurring_rule',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'recurring_rule']


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions."""
    
    class Meta:
        model = Transaction
        fields = [
            'account', 'category', 'description', 'gross_amount',
            'vat_percentage', 'competence_date', 'payment_date',
            'transaction_type', 'status', 'is_hypothetical',
            'external_reference', 'notes'
        ]

    def validate(self, data):
        # If status is 'paid', payment_date should be set
        if data.get('status') == 'paid' and not data.get('payment_date'):
            from django.utils import timezone
            data['payment_date'] = timezone.now().date()
        return data


class TransactionBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk transaction updates."""
    transaction_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    status = serializers.ChoiceField(
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled')],
        required=False
    )
    category_id = serializers.IntegerField(required=False)
    payment_date = serializers.DateField(required=False)


class TransactionImportSerializer(serializers.Serializer):
    """Serializer for CSV import endpoint."""
    csv_content = serializers.CharField()
    account_id = serializers.IntegerField()
    default_category_id = serializers.IntegerField(required=False, allow_null=True)
    date_format = serializers.CharField(default='%Y-%m-%d')
    skip_duplicates = serializers.BooleanField(default=True)
    delimiter = serializers.CharField(default=',', max_length=1)


class CashflowSummarySerializer(serializers.Serializer):
    """Serializer for cashflow summary data."""
    period = serializers.CharField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_cashflow = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = serializers.IntegerField()
