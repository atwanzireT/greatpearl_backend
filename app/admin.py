from django.contrib import admin
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'created_at')
    search_fields = ('name', 'phone', 'id')
    list_filter = ('created_at',)
    readonly_fields = ('id', 'created_at', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MillingProcess)
class MillingProcessAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'initial_weight', 'hulled_weight', 'get_milling_cost', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__name', 'id')
    readonly_fields = ('created_at', 'get_milling_cost')
    fieldsets = (
        (None, {
            'fields': ('customer', 'initial_weight', 'hulled_weight', 'milling_rate')
        }),
        ('Status', {
            'fields': ('status', 'completed_at', 'notes')
        }),
        ('Read Only', {
            'fields': ('created_at', 'get_milling_cost')
        }),
    )

    def get_milling_cost(self, obj):
        return obj.milling_cost
    get_milling_cost.short_description = 'Milling Cost'
    get_milling_cost.admin_order_field = 'hulled_weight'

@admin.register(CustomerAccount)
class CustomerAccountAdmin(admin.ModelAdmin):
    list_display = ('customer', 'balance', 'last_updated')
    search_fields = ('customer__name',)
    readonly_fields = ('last_updated',)

@admin.register(MillingTransaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'amount', 'transaction_type', 'reference', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('account__customer__name', 'reference')
    readonly_fields = ('created_at',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'email')
    search_fields = ('name', 'phone')
    readonly_fields = ('id', 'created_at', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CoffeePurchase)
class CoffeePurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'coffee_category', 'coffee_type', 'quantity', 'bags', 'reference_price', 'total_cost_display', 'payment_status', 'assessment', 'purchase_date', 'delivery_date', 'recorded_by')
    list_filter = ('coffee_category', 'coffee_type', 'payment_status', 'assessment', 'purchase_date')
    search_fields = ('supplier__name', 'notes')
    readonly_fields = ('total_cost_display', 'recorded_by')
    date_hierarchy = 'purchase_date'
    ordering = ('-purchase_date',)

    fieldsets = (
        ('Supplier & Coffee Info', {'fields': ('supplier', 'coffee_category', 'coffee_type', 'quantity', 'bags', 'reference_price')}),
        ('Status & Dates', {'fields': ('payment_status', 'assessment', 'purchase_date', 'delivery_date')}),
        ('Additional', {'fields': ('notes', 'total_cost_display', 'recorded_by')}),
    )

    def total_cost_display(self, obj):
        return f"{obj.total_cost:,.2f} UGX"
    total_cost_display.short_description = "Total Cost"

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.recorded_by_id:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CoffeeSale)
class CoffeeSaleAdmin(admin.ModelAdmin):
    list_display = ('customer', 'coffee_type', 'quantity', 'unit_price', 'total_amount', 'sale_date')
    list_filter = ('coffee_type', 'sale_date')
    search_fields = ('customer__name',)
    readonly_fields = ('total_amount', 'recorded_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'coffee',
        'moisture_content',
        'group1_defects',
        'group2_defects',
        'below_screen_12',
        'outturn',
        'actual_outturn_display',
        'outturn_price_display',
        'foreign_matter_penalty_display',
        'final_price_display',
    ]

    readonly_fields = [
        'actual_outturn_display',
        'outturn_price_display',
        'foreign_matter_penalty_display',
        'final_price_display',
    ]

    def actual_outturn_display(self, obj):
        return round(obj.actual_outturn, 2) if obj.actual_outturn is not None else "N/A"
    actual_outturn_display.short_description = 'Actual Outturn'

    def outturn_price_display(self, obj):
        return round(obj.outturn_price, 2) if obj.outturn_price is not None else "REJECT"
    outturn_price_display.short_description = 'Outturn Price'

    def foreign_matter_penalty_display(self, obj):
        return round(obj.foreign_matter_penalty, 2)
    foreign_matter_penalty_display.short_description = 'FM Penalty'

    def final_price_display(self, obj):
        return obj.final_price
    final_price_display.short_description = 'Final Price'
