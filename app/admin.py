from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Customer, CoffeeMilling, Payment

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for Customer model."""
    list_display = ('name', 'phone', 'email', 'gender', 'registered_at')
    list_filter = ('gender', 'registered_at')
    search_fields = ('name', 'phone', 'email')
    
    def get_readonly_fields(self, request, obj=None):
        """Make registered_at read-only."""
        return ['registered_at']

@admin.register(CoffeeMilling)
class CoffeeMillingAdmin(admin.ModelAdmin):
    pass
    # """Admin configuration for CoffeeMilling model."""
    # list_display = ('customer', 'raw_coffee_weight', 'hulled_coffee_weight', 
    #                 'coffee_type', 'milling_date', 'total_cost', 'milling_status')
    # list_filter = ('coffee_type', 'milling_date', 'milling_status')
    # search_fields = ('customer__name', 'customer__phone')
    
    # def get_readonly_fields(self, request, obj=None):
    #     """Make total_cost read-only."""
    #     return ['total_cost']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""
    list_display = ('customer', 'milling_record', 'amount_paid', 
                    'payment_method', 'payment_status', 'paid_at')
    list_filter = ('payment_method', 'payment_status', 'paid_at')
    search_fields = ('customer__name', 'customer__phone')