from django.contrib import admin
from django.utils.html import format_html
from .models import Bank, Account


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'swift_code', 'abi_code', 'country', 'is_active', 'accounts_count')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'swift_code', 'abi_code')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Bank Codes', {
            'fields': ('abi_code', 'swift_code', 'country')
        }),
        ('Additional Info', {
            'fields': ('website', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def accounts_count(self, obj):
        return obj.accounts.count()
    accounts_count.short_description = "Accounts"


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'bank', 'account_type', 'currency', 
        'initial_balance_display', 'current_balance_display',
        'is_active', 'include_in_totals'
    )
    list_filter = ('is_active', 'include_in_totals', 'account_type', 'currency', 'bank')
    search_fields = ('name', 'iban', 'bank__name')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'current_balance_display')
    raw_id_fields = ('bank',)

    fieldsets = (
        (None, {
            'fields': ('name', 'bank', 'account_type', 'is_active')
        }),
        ('Account Details', {
            'fields': ('iban', 'currency', 'initial_balance', 'current_balance_display')
        }),
        ('Display Settings', {
            'fields': ('include_in_totals', 'color', 'description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def initial_balance_display(self, obj):
        return f"{obj.initial_balance:,.2f} {obj.currency}"
    initial_balance_display.short_description = "Initial Balance"

    def current_balance_display(self, obj):
        try:
            balance = obj.current_balance
            color = 'green' if balance >= 0 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:,.2f} {}</span>',
                color, balance, obj.currency
            )
        except Exception:
            return format_html(
                '<span style="color: gray;">N/A</span>'
            )
    current_balance_display.short_description = "Current Balance"
