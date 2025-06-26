from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum
from .models import *
from .forms import *
from django.db.models import Sum, Count, Q, F
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta


class BaseView(LoginRequiredMixin):
    login_url = '/accounts/login/'
    template_name = 'base.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        return context
    
    def get_page_title(self):
        return getattr(self, 'page_title', 'Default Page Title')



# Dashboard
def index(request):
    # Date ranges
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    # Customer analytics
    total_customers = Customer.objects.count()
    new_customers_week = Customer.objects.filter(created_at__date__gte=last_week).count()
    
    # Milling analytics
    milling_stats = MillingProcess.objects.aggregate(
        pending=Count('id', filter=Q(status='P')),
        completed=Count('id', filter=Q(status='C')),
        total_hulled=Sum('hulled_weight', filter=Q(status='C'))
    )
    
    # Financial analytics
    financials = MillingTransaction.objects.aggregate(
        revenue=Sum('amount', filter=Q(transaction_type='C')),
        debits=Sum('amount', filter=Q(transaction_type='D'))
    )
    net_balance = (financials['revenue'] or 0) - (financials['debits'] or 0)
    
    # Coffee inventory
    purchases = CoffeePurchase.objects.aggregate(
        total_kg=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('unit_price'))
    )
    avg_purchase_price = (purchases['total_cost'] / purchases['total_kg']) if purchases['total_kg'] else 0
    
    # Sales analytics
    sales = CoffeeSale.objects.aggregate(
        total_kg=Sum('quantity'),
        total_amount=Sum(F('quantity') * F('unit_price'))
    )
    avg_sale_price = (sales['total_amount'] / sales['total_kg']) if sales['total_kg'] else 0
    
    # Top customers by milling volume
    top_customers = Customer.objects.annotate(
        milling_volume=Sum('milling_processes__hulled_weight')
    ).exclude(milling_volume=None).order_by('-milling_volume')[:5]
    
    # Recent transactions
    recent_transactions = MillingTransaction.objects.select_related('account__customer').order_by('-created_at')[:5]
    
    # Recent sales
    recent_sales = CoffeeSale.objects.select_related('recorded_by').order_by('-sale_date')[:5]
    
    context = {
        'page_title': 'Dashboard',
        'total_customers': total_customers,
        'new_customers_week': new_customers_week,
        'pending_milling': milling_stats['pending'] or 0,
        'completed_milling': milling_stats['completed'] or 0,
        'total_hulled': milling_stats['total_hulled'] or 0,
        'total_revenue': financials['revenue'] or 0,
        'total_debits': financials['debits'] or 0,
        'net_balance': net_balance,
        'purchases': {
            'total_kg': purchases['total_kg'] or 0,
            'total_cost': purchases['total_cost'] or 0,
            'avg_price': avg_purchase_price,
        },
        'sales': {
            'total_kg': sales['total_kg'] or 0,
            'total_amount': sales['total_amount'] or 0,
            'avg_price': avg_sale_price,
        },
        'top_customers': top_customers,
        'recent_transactions': recent_transactions,
        'recent_sales': recent_sales,
    }
    return render(request, 'index.html', context)

# Customer Views
class CustomerListView(BaseView, ListView):
    model = Customer
    template_name = 'customer_list.html'
    context_object_name = 'customers'
    paginate_by = 10
    page_title = 'Customers'
    ordering = ['-created_at']

class CustomerCreateView(BaseView, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer_form.html'
    success_url = reverse_lazy('customer_list')
    page_title = 'Add New Customer'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Customer created successfully!')
        return super().form_valid(form)

class CustomerUpdateView(BaseView, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer_form.html'
    success_url = reverse_lazy('customer_list')
    page_title = 'Update Customer'
    
    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully!')
        return super().form_valid(form)

class CustomerDetailView(BaseView, DetailView):
    model = Customer
    template_name = 'customer_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context['page_title'] = f'Customer: {customer.name}'
        context['milling_processes'] = customer.milling_processes.all().order_by('-created_at')[:5]
        context['transactions'] = MillingTransaction.objects.filter(account__customer=customer).order_by('-created_at')[:5]
        return context

# Milling Process Views
class MillingProcessListView(BaseView, ListView):
    model = MillingProcess
    template_name = 'milling_list.html'
    context_object_name = 'milling_processes'
    paginate_by = 10
    page_title = 'Milling Processes'
    ordering = ['-created_at']

class MillingProcessCreateView(BaseView, CreateView):
    model = MillingProcess
    form_class = MillingProcessForm
    template_name = 'milling_form.html'
    page_title = 'Add Milling Process'
    
    def get_success_url(self):
        # Redirect to transaction create view with milling ID in URL
        return reverse('transaction_create')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Milling process created successfully! Now record the payment.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
            return self.form_invalid(form)


class MillingDetailView(BaseView, DetailView):
    model = MillingProcess
    template_name = 'milling_detail.html'
    context_object_name = 'milling'

# Transaction Views
class TransactionListView(BaseView, ListView):
    model = MillingTransaction
    template_name = 'transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 10
    page_title = 'Transactions'
    ordering = ['-created_at']

class TransactionCreateView(BaseView, CreateView):
    model = MillingTransaction
    form_class = TransactionForm
    template_name = 'transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    page_title = 'Record Transaction'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Transaction recorded successfully!')
            return response
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

class TransactionDetailView(BaseView, DetailView):
    model = MillingTransaction
    template_name = "transaction_detail.html"
    context_object_name = "transaction"

# Supplier Views
class SupplierListView(BaseView, ListView):
    model = Supplier
    template_name = 'supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10
    page_title = 'Suppliers'
    ordering = ['name']

class SupplierCreateView(BaseView, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'supplier_form.html'
    success_url = reverse_lazy('supplier_list')
    page_title = 'Add Supplier'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Supplier created successfully!')
        return super().form_valid(form)

# Coffee Purchase Views
class CoffeePurchaseListView(BaseView, ListView):
    model = CoffeePurchase
    template_name = 'purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 10
    page_title = 'Coffee Purchases'
    ordering = ['-purchase_date']

class CoffeePurchaseCreateView(BaseView, CreateView):
    model = CoffeePurchase
    form_class = CoffeePurchaseForm
    template_name = 'purchase_form.html'
    success_url = reverse_lazy('purchase_list')
    page_title = 'Record Coffee Purchase'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Coffee purchase recorded successfully!')
        return super().form_valid(form)

# Coffee Sale Views
class CoffeeSaleListView(BaseView, ListView):
    model = CoffeeSale
    template_name = 'sale_list.html'
    context_object_name = 'sales'
    paginate_by = 10
    page_title = 'Coffee Sales'
    ordering = ['-sale_date']

class CoffeeSaleCreateView(BaseView, CreateView):
    model = CoffeeSale
    form_class = CoffeeSaleForm
    template_name = 'sale_form.html'
    success_url = reverse_lazy('sale_list')
    page_title = 'Record Coffee Sale'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Coffee sale recorded successfully!')
        return super().form_valid(form)
    


def customer_search(request):
    search_term = request.GET.get('q', '').strip()
    
    if not search_term:
        return JsonResponse({'error': 'No search term provided'}, status=400)
    
    customers = Customer.objects.filter(
        Q(name__icontains=search_term) | 
        Q(phone__icontains=search_term)
    ).order_by('name')[:10]
    
    results = [
        {
            'id': customer.id,
            'text': f"{customer.name} ({customer.phone})",
            'name': customer.name,
            'phone': customer.phone
        }
        for customer in customers
    ]
    
    return JsonResponse({'results': results})


class InventoryListView(BaseView, ListView):
    model = CoffeeInventory
    template_name = 'inventory_list.html'
    context_object_name = 'inventory_items'
    page_title = 'Coffee Inventory'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all inventory items for statistics
        all_items = CoffeeInventory.objects.all()

        # Calculate statistics
        context['total_items'] = all_items.count()
        total_quantity = all_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_value = all_items.aggregate(Sum('current_value'))['current_value__sum'] or 0

        context['total_quantity'] = total_quantity
        context['total_value'] = total_value

        # Calculate average cost per kg
        context['average_cost_per_kg'] = (total_value / total_quantity) if total_quantity > 0 else 0

        # Low stock items (less than 10kg)
        context['low_stock_items'] = all_items.filter(quantity__lt=10)

        # Inventory by category breakdown
        categories = []
        for category_code, category_name in CoffeeInventory.COFFEE_CATEGORIES:
            category_items = all_items.filter(coffee_category=category_code)
            cat_quantity = category_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
            cat_value = category_items.aggregate(Sum('current_value'))['current_value__sum'] or 0

            # Calculate percentage of total value
            percentage = (cat_value / total_value * 100) if total_value > 0 else 0

            categories.append({
                'coffee_category': category_code,
                'coffee_category_display': category_name,
                'total_quantity': cat_quantity,
                'total_value': cat_value,
                'percentage': percentage,
                'average_cost': (cat_value / cat_quantity) if cat_quantity > 0 else 0
            })

        context['inventory_by_category'] = categories

        return context


# Detail Views

class InventoryDetailView(BaseView, DetailView):
    model = CoffeeInventory
    template_name = 'inventory_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inventory = self.object
        context['page_title'] = f"{inventory.get_coffee_type_display()} Inventory"
        context['purchases'] = CoffeePurchase.objects.filter(
            coffee_type=inventory.coffee_type
        ).order_by('-purchase_date')[:10]
        context['sales'] = CoffeeSale.objects.filter(
            coffee_type=inventory.coffee_type
        ).order_by('-sale_date')[:10]
        return context
    

class MillingProcessDetailView(BaseView, DetailView):
    model = MillingProcess
    template_name = 'milling_detail.html'
    context_object_name = 'milling'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milling = self.object
        context['page_title'] = f'Milling Process #{milling.id}'
        context['transactions'] = milling.transactions.all()
        return context

class SupplierDetailView(BaseView, DetailView):
    model = Supplier
    template_name = 'supplier_detail.html'
    context_object_name = 'supplier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.object
        context['page_title'] = f'Supplier: {supplier.name}'
        context['purchases'] = supplier.purchases.all().order_by('-purchase_date')[:10]
        context['total_purchases'] = supplier.purchases.count()
        context['total_quantity'] = supplier.purchases.aggregate(Sum('quantity'))['quantity__sum'] or 0
        context['total_spent'] = sum(purchase.total_cost for purchase in supplier.purchases.all())
        return context

class CoffeePurchaseDetailView(BaseView, DetailView):
    model = CoffeePurchase
    template_name = 'purchase_detail.html'
    context_object_name = 'purchase'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase = self.object
        context['page_title'] = f'Purchase #{purchase.id}'
        return context

class CoffeeSaleDetailView(BaseView, DetailView):
    model = CoffeeSale
    template_name = 'sale_detail.html'
    context_object_name = 'sale'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sale = self.object
        context['page_title'] = f'Sale #{sale.id}'
        return context