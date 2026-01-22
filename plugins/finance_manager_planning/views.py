from decimal import Decimal
from datetime import date

from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication

from .models import Budget, RecurrenceRule, TaxConfig
from .serializers import (
    BudgetSerializer, BudgetCreateSerializer,
    RecurrenceRuleSerializer, RecurrenceRuleCreateSerializer,
    TaxConfigSerializer, TaxConfigCreateSerializer,
    ForecastRequestSerializer
)
from .logic_forecasting import generate_forecast


class BudgetListCreateView(generics.ListCreateAPIView):
    """
    GET: List all budgets
    POST: Create a new budget
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetCreateSerializer
        return BudgetSerializer

    def get_queryset(self):
        qs = Budget.objects.select_related('category', 'account')
        params = self.request.query_params
        
        # Filter by active status
        is_active = params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Filter by category
        category_id = params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        
        # Filter by account
        account_id = params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        
        # Filter by period
        period = params.get('period')
        if period:
            qs = qs.filter(period=period)
        
        # Filter current/active budgets
        current = params.get('current')
        if current and current.lower() == 'true':
            today = timezone.now().date()
            qs = qs.filter(
                is_active=True,
                start_date__lte=today
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            )
        
        # Filter over-budget
        over_budget = params.get('over_budget')
        if over_budget and over_budget.lower() == 'true':
            # This is computed, so we filter in Python
            qs = [b for b in qs if b.is_over_budget]
            return qs
        
        return qs.order_by('-start_date', 'category__name')


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a budget with current usage
    PUT/PATCH: Update a budget
    DELETE: Delete a budget
    """
    queryset = Budget.objects.select_related('category', 'account')
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BudgetCreateSerializer
        return BudgetSerializer


class BudgetStatusView(APIView):
    """
    GET: Get status overview of all active budgets.
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        today = timezone.now().date()
        
        budgets = Budget.objects.filter(
            is_active=True,
            start_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).select_related('category', 'account')
        
        results = {
            'total_budgets': budgets.count(),
            'over_budget': [],
            'near_limit': [],
            'healthy': []
        }
        
        for budget in budgets:
            amount, percentage = budget.get_current_usage()
            budget_data = {
                'id': budget.id,
                'category': budget.category.name,
                'target': float(budget.target_value),
                'current': float(amount),
                'percentage': float(percentage),
                'period': budget.period
            }
            
            if percentage > 100:
                results['over_budget'].append(budget_data)
            elif percentage >= budget.alert_threshold:
                results['near_limit'].append(budget_data)
            else:
                results['healthy'].append(budget_data)
        
        return Response(results)


class RecurrenceRuleListCreateView(generics.ListCreateAPIView):
    """
    GET: List all recurrence rules
    POST: Create a new recurrence rule
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecurrenceRuleCreateSerializer
        return RecurrenceRuleSerializer

    def get_queryset(self):
        qs = RecurrenceRule.objects.select_related('account', 'category')
        params = self.request.query_params
        
        # Filter by active status
        is_active = params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Filter by account
        account_id = params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        
        # Filter by category
        category_id = params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        
        # Filter by frequency
        frequency = params.get('frequency')
        if frequency:
            qs = qs.filter(frequency=frequency)
        
        # Filter by transaction type
        transaction_type = params.get('type')
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        
        # Search
        search = params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return qs.order_by('name')


class RecurrenceRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a recurrence rule
    PUT/PATCH: Update a recurrence rule
    DELETE: Delete a recurrence rule
    """
    queryset = RecurrenceRule.objects.select_related('account', 'category')
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RecurrenceRuleCreateSerializer
        return RecurrenceRuleSerializer


class RecurrenceRuleGenerateView(APIView):
    """
    POST: Manually trigger transaction generation for a recurrence rule.
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        try:
            rule = RecurrenceRule.objects.get(pk=pk)
        except RecurrenceRule.DoesNotExist:
            return Response(
                {'error': 'Recurrence rule not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not rule.is_active:
            return Response(
                {'error': 'Recurrence rule is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the date to generate for
        for_date_str = request.data.get('for_date')
        if for_date_str:
            from datetime import datetime
            try:
                for_date = datetime.strptime(for_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            for_date = timezone.now().date()
        
        transaction = rule.generate_transaction(for_date=for_date)
        
        from plugins.finance_manager_core.serializers import TransactionSerializer
        serializer = TransactionSerializer(transaction)
        
        return Response({
            'message': 'Transaction generated successfully',
            'transaction': serializer.data
        }, status=status.HTTP_201_CREATED)


class TaxConfigListCreateView(generics.ListCreateAPIView):
    """
    GET: List all tax configurations
    POST: Create a new tax configuration
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaxConfigCreateSerializer
        return TaxConfigSerializer

    def get_queryset(self):
        qs = TaxConfig.objects.prefetch_related('applicable_categories')
        params = self.request.query_params
        
        # Filter by active status
        is_active = params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Filter by applicable_to
        applicable_to = params.get('applicable_to')
        if applicable_to:
            qs = qs.filter(applicable_to=applicable_to)
        
        # Filter currently valid
        current = params.get('current')
        if current and current.lower() == 'true':
            today = timezone.now().date()
            qs = qs.filter(
                is_active=True,
                valid_from__lte=today
            ).filter(
                Q(valid_until__isnull=True) | Q(valid_until__gte=today)
            )
        
        return qs.order_by('name')


class TaxConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a tax configuration
    PUT/PATCH: Update a tax configuration
    DELETE: Delete a tax configuration
    """
    queryset = TaxConfig.objects.prefetch_related('applicable_categories')
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaxConfigCreateSerializer
        return TaxConfigSerializer


class TaxCalculateView(APIView):
    """
    POST: Calculate tax for a given amount.
    
    Body: { "amount": 1000.00, "tax_config_id": 1 }
    Or: { "amount": 1000.00 } to use all applicable taxes
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
        except Exception:
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tax_config_id = request.data.get('tax_config_id')
        
        if tax_config_id:
            try:
                config = TaxConfig.objects.get(pk=tax_config_id, is_active=True)
                tax_amount = config.calculate_tax(amount)
                return Response({
                    'amount': float(amount),
                    'tax_config': config.name,
                    'tax_rate': float(config.percentage),
                    'tax_amount': float(tax_amount),
                    'net_amount': float(amount - tax_amount)
                })
            except TaxConfig.DoesNotExist:
                return Response(
                    {'error': 'Tax configuration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Calculate using all applicable income taxes
        today = timezone.now().date()
        configs = TaxConfig.objects.filter(
            is_active=True,
            applicable_to='income',
            valid_from__lte=today
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=today)
        )
        
        total_tax = Decimal('0.00')
        breakdown = []
        
        for config in configs:
            tax = config.calculate_tax(amount)
            if tax > 0:
                total_tax += tax
                breakdown.append({
                    'name': config.name,
                    'rate': float(config.percentage),
                    'amount': float(tax)
                })
        
        return Response({
            'amount': float(amount),
            'total_tax': float(total_tax),
            'net_amount': float(amount - total_tax),
            'breakdown': breakdown
        })


class CashflowForecastView(APIView):
    """
    POST: Generate a cashflow forecast.
    
    Body: {
        "months": 3,
        "account_ids": [1, 2],  // optional
        "include_hypothetical": true,
        "include_recurring": true,
        "use_historical_averages": true,
        "historical_months": 6
    }
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = ForecastRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        result = generate_forecast(
            months=data['months'],
            account_ids=data.get('account_ids'),
            include_hypothetical=data.get('include_hypothetical', True),
            include_recurring=data.get('include_recurring', True),
            use_historical_averages=data.get('use_historical_averages', True),
            historical_months=data.get('historical_months', 6)
        )
        
        return Response(result)

    def get(self, request):
        """GET shortcut for common forecast durations."""
        months = request.query_params.get('months', '3')
        try:
            months = int(months)
        except ValueError:
            months = 3
        
        account_ids = request.query_params.get('account_ids')
        if account_ids:
            account_ids = [int(x) for x in account_ids.split(',') if x.strip().isdigit()]
        else:
            account_ids = None
        
        result = generate_forecast(
            months=months,
            account_ids=account_ids,
            include_hypothetical=True,
            include_recurring=True,
            use_historical_averages=True
        )
        
        return Response(result)
