from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Customer, CoffeeMilling, Payment

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for Customer model."""
    list_display = ('name', 'phone', 'registered_at')
    list_filter = ('registered_at',)
    search_fields = ('name', 'phone')
    
    def get_readonly_fields(self, request, obj=None):
        """Make registered_at read-only."""
        return ['registered_at']

@admin.register(CoffeeMilling)
class CoffeeMillingAdmin(admin.ModelAdmin):
    pass
    """Admin configuration for CoffeeMilling model."""
    list_display = ('customer', 'hulled_coffee_weight', 'milling_date', 'total_cost', 'milling_status')
    list_filter = ('milling_status',)
    search_fields = ('customer__name', 'customer__phone')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""
    list_display = ('customer', 'milling_record', 'amount_paid',  'paid_at')
    list_filter = ('customer', 'paid_at')
    search_fields = ('customer__name', 'customer__phone')