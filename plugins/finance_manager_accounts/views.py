from decimal import Decimal
from django.db.models import Sum, F
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication

from .models import Bank, Account
from .serializers import (
    BankSerializer, AccountSerializer, 
    AccountMinimalSerializer, AccountBalanceSerializer
)


class BankListCreateView(generics.ListCreateAPIView):
    """
    GET: List all banks
    POST: Create a new bank
    """
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        qs = Bank.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Search by name or code
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search) |
                models.Q(swift_code__icontains=search) |
                models.Q(abi_code__icontains=search)
            )
        
        return qs.order_by('name')


class BankDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a bank
    PUT/PATCH: Update a bank
    DELETE: Delete a bank
    """
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]


class AccountListCreateView(generics.ListCreateAPIView):
    """
    GET: List all accounts
    POST: Create a new account
    """
    queryset = Account.objects.select_related('bank')
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        qs = Account.objects.select_related('bank')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Filter by bank
        bank_id = self.request.query_params.get('bank')
        if bank_id:
            qs = qs.filter(bank_id=bank_id)
        
        # Filter by account type
        account_type = self.request.query_params.get('account_type')
        if account_type:
            qs = qs.filter(account_type=account_type)
        
        # Filter by currency
        currency = self.request.query_params.get('currency')
        if currency:
            qs = qs.filter(currency=currency.upper())
        
        # Filter by include_in_totals
        include_in_totals = self.request.query_params.get('include_in_totals')
        if include_in_totals is not None:
            qs = qs.filter(include_in_totals=include_in_totals.lower() == 'true')
        
        # Search by name or IBAN
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(iban__icontains=search) |
                Q(bank__name__icontains=search)
            )
        
        return qs.order_by('name')


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve an account with current balance
    PUT/PATCH: Update an account
    DELETE: Delete an account
    """
    queryset = Account.objects.select_related('bank')
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]


class AggregateBalanceView(APIView):
    """
    GET: Calculate aggregate balance across multiple accounts.
    
    Query params:
    - currency: Filter by currency (required for accurate aggregation)
    - include_inactive: Include inactive accounts (default: false)
    - account_ids: Comma-separated list of account IDs to include
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        currency = request.query_params.get('currency', 'EUR').upper()
        include_inactive = request.query_params.get('include_inactive', 'false').lower() == 'true'
        account_ids = request.query_params.get('account_ids')
        
        # Build base queryset
        qs = Account.objects.filter(
            currency=currency,
            include_in_totals=True
        ).select_related('bank')
        
        if not include_inactive:
            qs = qs.filter(is_active=True)
        
        if account_ids:
            ids = [int(x.strip()) for x in account_ids.split(',') if x.strip().isdigit()]
            qs = qs.filter(id__in=ids)
        
        # Calculate aggregate balance
        total_balance = Decimal('0.00')
        accounts_data = []
        
        for account in qs:
            try:
                balance = account.current_balance
                total_balance += balance
                accounts_data.append({
                    'id': account.id,
                    'name': account.name,
                    'bank_name': account.bank.name if account.bank else None,
                    'currency': account.currency,
                    'account_type': account.account_type,
                    'balance': balance
                })
            except Exception:
                # Skip accounts with calculation errors
                pass
        
        return Response({
            'total_balance': total_balance,
            'currency': currency,
            'accounts_count': len(accounts_data),
            'accounts': accounts_data
        }, status=status.HTTP_200_OK)


class AccountBalanceByTypeView(APIView):
    """
    GET: Get balance breakdown by account type.
    
    Query params:
    - currency: Filter by currency (default: EUR)
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        currency = request.query_params.get('currency', 'EUR').upper()
        
        accounts = Account.objects.filter(
            currency=currency,
            is_active=True,
            include_in_totals=True
        ).select_related('bank')
        
        breakdown = {}
        total = Decimal('0.00')
        
        for account in accounts:
            try:
                balance = account.current_balance
                account_type = account.account_type
                
                if account_type not in breakdown:
                    breakdown[account_type] = {
                        'type': account_type,
                        'display_name': account.get_account_type_display(),
                        'total_balance': Decimal('0.00'),
                        'accounts_count': 0
                    }
                
                breakdown[account_type]['total_balance'] += balance
                breakdown[account_type]['accounts_count'] += 1
                total += balance
            except Exception:
                pass
        
        return Response({
            'currency': currency,
            'total_balance': total,
            'breakdown': list(breakdown.values())
        }, status=status.HTTP_200_OK)
