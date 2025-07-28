from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name="home"),

    # Customer URLs
    path('customers/', customer_list, name='customer_list'),
    path('customers/<int:pk>/', customer_detail, name='customer_detail'),
    
    # Milling Process URLs
    path('milling/', milling_list, name='milling_list'),
    path('milling/<int:pk>/', milling_detail, name='milling_detail'),

    # Quality Assessment URLs
    path('assessments/', assessment_list, name='assessment_list'),
    path('assessments/<int:pk>/create/', assessment_create, name='assessment_create'),
    path('assessments/<int:pk>/', assessment_detail, name='assessment_detail'),
    
    # Transaction URLs
    path('transactions/', transaction_list, name='transaction_list'),
    path('transactions/<int:pk>/', transaction_detail, name='transaction_detail'),
    
    # Supplier URLs
    path('suppliers/', supplier_list, name='supplier_list'),
    path('suppliers/<int:pk>/', supplier_detail, name='supplier_detail'),
    
    # Coffee Purchase URLs
    path('purchases/', purchase_list, name='purchase_list'),
    path('purchases/<int:pk>/', purchase_detail, name='purchase_detail'),
    
    # Coffee Sale URLs
    path('sales/', sale_list, name='sale_list'),
    path('sales/<int:pk>/', sale_detail, name='sale_detail'),

    # Inventory URLs
    path('inventory/', inventory_dashboard, name='inventory_list'),
    path('inventory/<int:pk>/', inventory_detail, name='inventory_detail'),

    # Search URLs
    path('customer-search/', customer_search, name='customer_search'),
]