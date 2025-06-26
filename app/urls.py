from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name="index"),

    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    
    # Milling Process URLs
    path('milling/', MillingProcessListView.as_view(), name='milling_list'),
    path('milling/add/', MillingProcessCreateView.as_view(), name='milling_create'),
    
    # Transaction URLs
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/add/', TransactionCreateView.as_view(), name='transaction_create'),
    
    # Supplier URLs
    path('suppliers/', SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/add/', SupplierCreateView.as_view(), name='supplier_create'),
    
    # Coffee Purchase URLs
    path('purchases/', CoffeePurchaseListView.as_view(), name='purchase_list'),
    path('purchases/add/', CoffeePurchaseCreateView.as_view(), name='purchase_create'),
    
    # Coffee Sale URLs
    path('sales/', CoffeeSaleListView.as_view(), name='sale_list'),
    path('sales/add/', CoffeeSaleCreateView.as_view(), name='sale_create'),

    # Inventory
    path('inventory/', InventoryListView.as_view(), name='inventory_list'),
    path('inventory/<int:pk>/', InventoryDetailView.as_view(), name='inventory_detail'),
]