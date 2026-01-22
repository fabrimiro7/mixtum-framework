from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'colored_icon', 'parent', 'transaction_type',
        'is_active', 'sort_order', 'transactions_count'
    )
    list_filter = ('is_active', 'transaction_type', 'parent')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('parent',)

    fieldsets = (
        (None, {
            'fields': ('name', 'parent', 'transaction_type', 'is_active')
        }),
        ('Appearance', {
            'fields': ('color', 'icon', 'sort_order')
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

    def colored_icon(self, obj):
        if obj.icon:
            return format_html(
                '<span style="color: {};">{}</span>',
                obj.color, obj.icon
            )
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;'
            'background-color:{};border-radius:50%;"></span>',
            obj.color
        )
    colored_icon.short_description = "Icon"

    def transactions_count(self, obj):
        return obj.transactions.count()
    transactions_count.short_description = "Transactions"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'description_short', 'account', 'category',
        'amount_display', 'transaction_type', 'status',
        'competence_date', 'payment_date', 'is_hypothetical'
    )
    list_filter = (
        'transaction_type', 'status', 'is_hypothetical',
        'data_source', 'account', 'category', 'competence_date'
    )
    search_fields = ('description', 'external_reference', 'notes')
    ordering = ('-competence_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at', 'net_amount_display', 'vat_amount_display')
    raw_id_fields = ('account', 'category', 'recurring_rule')
    date_hierarchy = 'competence_date'

    fieldsets = (
        (None, {
            'fields': ('account', 'category', 'description')
        }),
        ('Amount', {
            'fields': (
                'gross_amount', 'vat_percentage',
                'net_amount_display', 'vat_amount_display'
            )
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_type', 'status', 'is_hypothetical',
                'competence_date', 'payment_date'
            )
        }),
        ('Source & Reference', {
            'fields': ('data_source', 'external_reference', 'recurring_rule'),
            'classes': ('collapse',)
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

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"

    def amount_display(self, obj):
        if obj.transaction_type == 'income':
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = '-'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{:,.2f}</span>',
            color, sign, obj.gross_amount
        )
    amount_display.short_description = "Amount"
    amount_display.admin_order_field = 'gross_amount'

    def net_amount_display(self, obj):
        return f"{obj.net_amount:,.2f}"
    net_amount_display.short_description = "Net Amount"

    def vat_amount_display(self, obj):
        return f"{obj.vat_amount:,.2f} ({obj.vat_percentage}%)"
    vat_amount_display.short_description = "VAT Amount"

    actions = ['mark_as_paid', 'mark_as_pending', 'mark_as_cancelled']

    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        updated = queryset.exclude(status='paid').update(
            status='paid',
            payment_date=timezone.now().date()
        )
        self.message_user(request, f'{updated} transactions marked as paid.')
    mark_as_paid.short_description = "Mark selected as paid"

    def mark_as_pending(self, request, queryset):
        updated = queryset.exclude(status='pending').update(status='pending')
        self.message_user(request, f'{updated} transactions marked as pending.')
    mark_as_pending.short_description = "Mark selected as pending"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(status='cancelled').update(status='cancelled')
        self.message_user(request, f'{updated} transactions marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected as cancelled"
