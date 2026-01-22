from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta

from django.db.models import Sum, Count, Q, Case, When, F, DecimalField
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication

from .models import Category, Transaction
from .serializers import (
    CategorySerializer, CategoryMinimalSerializer, CategoryTreeSerializer,
    TransactionSerializer, TransactionCreateSerializer,
    TransactionBulkUpdateSerializer, TransactionImportSerializer,
    CashflowSummarySerializer
)
from .services import import_transactions_from_csv


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET: List all categories
    POST: Create a new category
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        qs = Category.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Filter top-level only
        top_level = self.request.query_params.get('top_level')
        if top_level and top_level.lower() == 'true':
            qs = qs.filter(parent__isnull=True)
        
        # Filter by parent
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            if parent_id == 'null':
                qs = qs.filter(parent__isnull=True)
            else:
                qs = qs.filter(parent_id=parent_id)
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            qs = qs.filter(
                Q(transaction_type=transaction_type) | 
                Q(transaction_type__isnull=True)
            )
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        
        return qs.order_by('sort_order', 'name')


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a category
    PUT/PATCH: Update a category
    DELETE: Delete a category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]


class CategoryTreeView(APIView):
    """
    GET: Get the full category tree structure.
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        # Get only top-level categories, tree serializer handles children
        categories = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).order_by('sort_order', 'name')
        
        serializer = CategoryTreeSerializer(categories, many=True)
        return Response(serializer.data)


class TransactionListCreateView(generics.ListCreateAPIView):
    """
    GET: List transactions with filtering
    POST: Create a new transaction
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TransactionCreateSerializer
        return TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.select_related('account', 'category', 'account__bank')
        params = self.request.query_params
        
        # Filter by account
        account_id = params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        
        # Filter by category
        category_id = params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        
        # Filter by transaction type
        transaction_type = params.get('type')
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        
        # Filter by status
        status_filter = params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # Filter by hypothetical
        is_hypothetical = params.get('is_hypothetical')
        if is_hypothetical is not None:
            qs = qs.filter(is_hypothetical=is_hypothetical.lower() == 'true')
        
        # Date range filters
        date_from = params.get('from')
        date_to = params.get('to')
        if date_from:
            qs = qs.filter(competence_date__gte=date_from)
        if date_to:
            qs = qs.filter(competence_date__lte=date_to)
        
        # Period shortcuts
        period = params.get('period')
        today = timezone.now().date()
        if period == 'this_month':
            start = date(today.year, today.month, 1)
            qs = qs.filter(competence_date__gte=start)
        elif period == 'last_month':
            start = date(today.year, today.month, 1) - relativedelta(months=1)
            end = date(today.year, today.month, 1) - relativedelta(days=1)
            qs = qs.filter(competence_date__gte=start, competence_date__lte=end)
        elif period == 'this_year':
            start = date(today.year, 1, 1)
            qs = qs.filter(competence_date__gte=start)
        elif period == 'last_3_months':
            start = today - relativedelta(months=3)
            qs = qs.filter(competence_date__gte=start)
        
        # Overdue filter
        overdue = params.get('overdue')
        if overdue and overdue.lower() == 'true':
            qs = qs.filter(
                status__in=['pending', 'scheduled'],
                competence_date__lt=today
            )
        
        # Search
        search = params.get('search')
        if search:
            qs = qs.filter(
                Q(description__icontains=search) |
                Q(external_reference__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # Ordering
        ordering = params.get('ordering', '-competence_date')
        allowed_ordering = {
            'competence_date', '-competence_date',
            'gross_amount', '-gross_amount',
            'created_at', '-created_at',
            'payment_date', '-payment_date'
        }
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-competence_date')
        
        return qs


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a transaction
    PUT/PATCH: Update a transaction
    DELETE: Delete a transaction
    """
    queryset = Transaction.objects.select_related('account', 'category', 'account__bank')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]


class TransactionBulkUpdateView(APIView):
    """
    POST: Bulk update multiple transactions.
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = TransactionBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        transaction_ids = data['transaction_ids']
        
        transactions = Transaction.objects.filter(id__in=transaction_ids)
        updated_count = 0
        
        update_fields = []
        if 'status' in data:
            transactions = transactions.exclude(status=data['status'])
            update_data = {'status': data['status']}
            update_fields.append('status')
            
            if data['status'] == 'paid' and 'payment_date' in data:
                update_data['payment_date'] = data['payment_date']
                update_fields.append('payment_date')
            elif data['status'] == 'paid':
                update_data['payment_date'] = timezone.now().date()
                update_fields.append('payment_date')
        
        if 'category_id' in data:
            update_data['category_id'] = data['category_id']
            update_fields.append('category_id')
        
        if update_fields:
            updated_count = transactions.update(**update_data)
        
        return Response({
            'updated_count': updated_count,
            'message': f'Successfully updated {updated_count} transactions'
        })


class TransactionMarkPaidView(APIView):
    """
    POST: Mark a transaction as paid.
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        payment_date = request.data.get('payment_date')
        if payment_date:
            from datetime import datetime
            try:
                payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        transaction.mark_as_paid(payment_date)
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)


class TransactionImportView(APIView):
    """
    POST: Import transactions from CSV.
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = TransactionImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        result = import_transactions_from_csv(
            account_id=data['account_id'],
            csv_content=data['csv_content'],
            category_id=data.get('default_category_id'),
            date_format=data.get('date_format', '%Y-%m-%d'),
            skip_duplicates=data.get('skip_duplicates', True),
            delimiter=data.get('delimiter', ',')
        )
        
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)


class CashflowSummaryView(APIView):
    """
    GET: Get cashflow summary aggregated by month or year.
    
    Query params:
    - granularity: 'month' or 'year' (default: month)
    - from: Start date (YYYY-MM-DD)
    - to: End date (YYYY-MM-DD)
    - account: Filter by account ID
    - include_hypothetical: Include hypothetical transactions (default: false)
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        params = request.query_params
        granularity = params.get('granularity', 'month').lower()
        
        if granularity not in ('month', 'year'):
            return Response(
                {'error': "granularity must be 'month' or 'year'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        qs = Transaction.objects.filter(status__in=['pending', 'paid', 'scheduled'])
        
        # Account filter
        account_id = params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        
        # Hypothetical filter
        include_hypothetical = params.get('include_hypothetical', 'false').lower() == 'true'
        if not include_hypothetical:
            qs = qs.filter(is_hypothetical=False)
        
        # Date range
        date_from = params.get('from')
        date_to = params.get('to')
        if date_from:
            qs = qs.filter(competence_date__gte=date_from)
        if date_to:
            qs = qs.filter(competence_date__lte=date_to)
        
        # Aggregate
        trunc = TruncMonth if granularity == 'month' else TruncYear
        tz = timezone.get_current_timezone()
        
        aggregated = (
            qs.annotate(period=trunc('competence_date', tzinfo=tz))
            .values('period')
            .annotate(
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
                ),
                transaction_count=Count('id')
            )
            .order_by('period')
        )
        
        results = []
        for row in aggregated:
            period_date = row['period']
            if granularity == 'month':
                period_str = period_date.strftime('%Y-%m')
                period_start = date(period_date.year, period_date.month, 1)
                period_end = period_start + relativedelta(months=1) - relativedelta(days=1)
            else:
                period_str = period_date.strftime('%Y')
                period_start = date(period_date.year, 1, 1)
                period_end = date(period_date.year, 12, 31)
            
            income = row['total_income'] or Decimal('0.00')
            expenses = row['total_expenses'] or Decimal('0.00')
            
            results.append({
                'period': period_str,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'total_income': income,
                'total_expenses': expenses,
                'net_cashflow': income - expenses,
                'transaction_count': row['transaction_count']
            })
        
        return Response({
            'granularity': granularity,
            'results': results
        })


class CategoryBreakdownView(APIView):
    """
    GET: Get transaction breakdown by category.
    
    Query params:
    - type: 'income' or 'expense'
    - from: Start date
    - to: End date
    - account: Filter by account ID
    """
    permission_classes = [IsAuthenticated]

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        params = request.query_params
        
        qs = Transaction.objects.filter(
            status__in=['pending', 'paid', 'scheduled'],
            is_hypothetical=False
        ).select_related('category')
        
        # Transaction type filter
        tx_type = params.get('type')
        if tx_type:
            qs = qs.filter(transaction_type=tx_type)
        
        # Account filter
        account_id = params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        
        # Date range
        date_from = params.get('from')
        date_to = params.get('to')
        if date_from:
            qs = qs.filter(competence_date__gte=date_from)
        if date_to:
            qs = qs.filter(competence_date__lte=date_to)
        
        # Aggregate by category
        breakdown = (
            qs.values('category__id', 'category__name', 'category__color')
            .annotate(
                total=Sum('gross_amount'),
                count=Count('id')
            )
            .order_by('-total')
        )
        
        results = []
        grand_total = Decimal('0.00')
        
        for row in breakdown:
            total = row['total'] or Decimal('0.00')
            grand_total += total
            results.append({
                'category_id': row['category__id'],
                'category_name': row['category__name'],
                'category_color': row['category__color'],
                'total': total,
                'count': row['count']
            })
        
        # Calculate percentages
        for item in results:
            if grand_total > 0:
                item['percentage'] = round((item['total'] / grand_total) * 100, 2)
            else:
                item['percentage'] = 0
        
        return Response({
            'grand_total': grand_total,
            'breakdown': results
        })
