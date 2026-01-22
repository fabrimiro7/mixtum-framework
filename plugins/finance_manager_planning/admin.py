from django.contrib import admin
from django.utils.html import format_html
from .models import Budget, RecurrenceRule, TaxConfig


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'account', 'target_value', 'period',
        'usage_display', 'alert_threshold', 'is_active', 'start_date'
    )
    list_filter = ('is_active', 'period', 'category', 'account')
    search_fields = ('category__name', 'account__name', 'notes')
    ordering = ('-start_date', 'category__name')
    readonly_fields = ('created_at', 'updated_at', 'usage_display')
    raw_id_fields = ('category', 'account')
    date_hierarchy = 'start_date'

    fieldsets = (
        (None, {
            'fields': ('category', 'account', 'is_active')
        }),
        ('Budget Settings', {
            'fields': ('target_value', 'period', 'alert_threshold')
        }),
        ('Current Status', {
            'fields': ('usage_display',),
        }),
        ('Validity', {
            'fields': ('start_date', 'end_date')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def usage_display(self, obj):
        try:
            amount, percentage = obj.get_current_usage()
            if percentage > 100:
                color = 'red'
                status = 'OVER BUDGET'
            elif percentage >= obj.alert_threshold:
                color = 'orange'
                status = 'Near Limit'
            else:
                color = 'green'
                status = 'OK'
            
            return format_html(
                '<span style="color: {};">{:,.2f} / {:,.2f} ({:.1f}%) - {}</span>',
                color, amount, obj.target_value, percentage, status
            )
        except Exception:
            return format_html('<span style="color: gray;">N/A</span>')
    usage_display.short_description = "Current Usage"


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'account', 'category', 'amount_display',
        'frequency', 'transaction_type', 'is_active',
        'next_occurrence_display', 'last_generated_date'
    )
    list_filter = ('is_active', 'frequency', 'transaction_type', 'account', 'category')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'last_generated_date', 'next_occurrence_display')
    raw_id_fields = ('account', 'category', 'template_transaction')

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active', 'template_transaction')
        }),
        ('Transaction Template', {
            'fields': (
                'account', 'category', 'description',
                'gross_amount', 'vat_percentage', 'transaction_type'
            )
        }),
        ('Schedule', {
            'fields': (
                'frequency', 'day_of_month', 'day_of_week',
                'start_date', 'end_date', 'last_generated_date',
                'next_occurrence_display'
            )
        }),
        ('Options', {
            'fields': ('generate_as_hypothetical', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def amount_display(self, obj):
        if obj.transaction_type == 'income':
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = '-'
        return format_html(
            '<span style="color: {};">{}{:,.2f}</span>',
            color, sign, obj.gross_amount
        )
    amount_display.short_description = "Amount"

    def next_occurrence_display(self, obj):
        next_date = obj.get_next_occurrence_date()
        if next_date:
            return next_date.strftime('%Y-%m-%d')
        return format_html('<span style="color: gray;">None</span>')
    next_occurrence_display.short_description = "Next Occurrence"

    actions = ['generate_transactions']

    def generate_transactions(self, request, queryset):
        from django.utils import timezone
        count = 0
        for rule in queryset.filter(is_active=True):
            try:
                rule.generate_transaction(for_date=timezone.now().date())
                count += 1
            except Exception:
                pass
        self.message_user(request, f'Generated transactions for {count} rules.')
    generate_transactions.short_description = "Generate transactions now"


@admin.register(TaxConfig)
class TaxConfigAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'percentage_display', 'applicable_to',
        'threshold_amount', 'is_progressive', 'is_active',
        'valid_from', 'valid_until'
    )
    list_filter = ('is_active', 'applicable_to', 'is_progressive')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('applicable_categories',)
    date_hierarchy = 'valid_from'

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Tax Rate', {
            'fields': ('percentage', 'threshold_amount', 'is_progressive')
        }),
        ('Applicability', {
            'fields': ('applicable_to', 'applicable_categories')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Details', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = "Rate"
