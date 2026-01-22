from django.urls import path
from .views import (
    BankListCreateView, BankDetailView,
    AccountListCreateView, AccountDetailView,
    AggregateBalanceView, AccountBalanceByTypeView
)

urlpatterns = [
    # Banks
    path('banks/', BankListCreateView.as_view(), name='bank-list'),
    path('banks/<int:pk>/', BankDetailView.as_view(), name='bank-detail'),
    
    # Accounts
    path('accounts/', AccountListCreateView.as_view(), name='account-list'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    
    # Aggregations
    path('accounts/aggregate-balance/', AggregateBalanceView.as_view(), name='aggregate-balance'),
    path('accounts/balance-by-type/', AccountBalanceByTypeView.as_view(), name='balance-by-type'),
]
