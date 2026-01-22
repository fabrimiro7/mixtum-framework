from rest_framework import serializers
from .models import Bank, Account


class BankSerializer(serializers.ModelSerializer):
    accounts_count = serializers.SerializerMethodField()

    class Meta:
        model = Bank
        fields = [
            'id', 'name', 'abi_code', 'swift_code', 'country',
            'website', 'notes', 'is_active', 'accounts_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_accounts_count(self, obj):
        return obj.accounts.filter(is_active=True).count()


class BankMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested representations."""
    
    class Meta:
        model = Bank
        fields = ['id', 'name', 'swift_code']


class AccountSerializer(serializers.ModelSerializer):
    bank = BankMinimalSerializer(read_only=True)
    bank_id = serializers.PrimaryKeyRelatedField(
        queryset=Bank.objects.all(),
        source='bank',
        write_only=True,
        required=False,
        allow_null=True
    )
    current_balance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    account_type_display = serializers.CharField(
        source='get_account_type_display',
        read_only=True
    )
    currency_display = serializers.CharField(
        source='get_currency_display',
        read_only=True
    )

    class Meta:
        model = Account
        fields = [
            'id', 'name', 'bank', 'bank_id', 'iban',
            'initial_balance', 'current_balance', 'currency', 'currency_display',
            'account_type', 'account_type_display', 'description',
            'is_active', 'include_in_totals', 'color',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'current_balance']


class AccountMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for dropdowns and nested representations."""
    bank_name = serializers.CharField(source='bank.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Account
        fields = ['id', 'name', 'bank_name', 'currency', 'account_type']


class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for aggregated balance information."""
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()
    accounts_count = serializers.IntegerField()
    accounts = AccountMinimalSerializer(many=True)
