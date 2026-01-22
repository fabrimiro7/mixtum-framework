from django.urls import path
from .views import (
    BudgetListCreateView, BudgetDetailView, BudgetStatusView,
    RecurrenceRuleListCreateView, RecurrenceRuleDetailView, RecurrenceRuleGenerateView,
    TaxConfigListCreateView, TaxConfigDetailView, TaxCalculateView,
    CashflowForecastView
)

urlpatterns = [
    # Budgets
    path('budgets/', BudgetListCreateView.as_view(), name='budget-list'),
    path('budgets/<int:pk>/', BudgetDetailView.as_view(), name='budget-detail'),
    path('budgets/status/', BudgetStatusView.as_view(), name='budget-status'),
    
    # Recurrence Rules
    path('recurrence-rules/', RecurrenceRuleListCreateView.as_view(), name='recurrence-rule-list'),
    path('recurrence-rules/<int:pk>/', RecurrenceRuleDetailView.as_view(), name='recurrence-rule-detail'),
    path('recurrence-rules/<int:pk>/generate/', RecurrenceRuleGenerateView.as_view(), name='recurrence-rule-generate'),
    
    # Tax Configurations
    path('tax-configs/', TaxConfigListCreateView.as_view(), name='tax-config-list'),
    path('tax-configs/<int:pk>/', TaxConfigDetailView.as_view(), name='tax-config-detail'),
    path('tax-configs/calculate/', TaxCalculateView.as_view(), name='tax-calculate'),
    
    # Forecasting
    path('forecast/', CashflowForecastView.as_view(), name='cashflow-forecast'),
]
