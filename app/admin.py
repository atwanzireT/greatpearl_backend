from django.contrib import admin
from .models import Customer, MillingProcess, CustomerAccount, MillingTransaction, Supplier, CoffeePurchase, CoffeeSale
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
    list_display = ('id', 'name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone')
    readonly_fields = ('id', 'created_at', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(CoffeePurchase)
class CoffeePurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'coffee_type', 'get_quantity', 'get_unit_price', 'get_total_cost', 'purchase_date')
    list_filter = ('coffee_type', 'purchase_date')
    search_fields = ('supplier__name',)
    readonly_fields = ('recorded_by', 'get_total_cost')
    fieldsets = (
        (None, {
            'fields': ('supplier', 'coffee_type', 'quantity', 'unit_price')
        }),
        ('Dates', {
            'fields': ('purchase_date', 'delivery_date')
        }),
        ('Other', {
            'fields': ('notes', 'recorded_by', 'get_total_cost')
        }),
    )

    def get_quantity(self, obj):
        return f"{obj.quantity} kg" if obj.quantity else "-"
    get_quantity.short_description = 'Quantity'

    def get_unit_price(self, obj):
        return f"Ugx. {obj.unit_price}" if obj.unit_price else "-"
    get_unit_price.short_description = 'Unit Price'

    def get_total_cost(self, obj):
        return f"Ugx. {obj.total_cost}" if obj.total_cost else "N/A"
    get_total_cost.short_description = 'Total Cost'

    def save_model(self, request, obj, form, change):
        if not obj.recorded_by_id:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['quantity'].widget.attrs['placeholder'] = 'e.g. 50.25'
        form.base_fields['unit_price'].widget.attrs['placeholder'] = 'e.g. 12.50'
        return form

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

