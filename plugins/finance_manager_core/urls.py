from django.urls import path
from .views import (
    CategoryListCreateView, CategoryDetailView, CategoryTreeView,
    TransactionListCreateView, TransactionDetailView,
    TransactionBulkUpdateView, TransactionMarkPaidView,
    TransactionImportView, CashflowSummaryView, CategoryBreakdownView
)

urlpatterns = [
    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/tree/', CategoryTreeView.as_view(), name='category-tree'),
    
    # Transactions
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/<int:pk>/mark-paid/', TransactionMarkPaidView.as_view(), name='transaction-mark-paid'),
    path('transactions/bulk-update/', TransactionBulkUpdateView.as_view(), name='transaction-bulk-update'),
    path('transactions/import/', TransactionImportView.as_view(), name='transaction-import'),
    
    # Analytics
    path('cashflow/summary/', CashflowSummaryView.as_view(), name='cashflow-summary'),
    path('cashflow/by-category/', CategoryBreakdownView.as_view(), name='category-breakdown'),
]
