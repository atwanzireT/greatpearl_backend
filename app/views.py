from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    Sum, Count, Avg, Q, Case, When, Value, IntegerField
)
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import (
    Customer, MillingProcess, MillingTransaction, Supplier,
    CoffeePurchase, CoffeeSale, CoffeeInventory, Assessment
)
from .forms import (
    CustomerForm, MillingProcessForm, SupplierForm, CoffeePurchaseForm,
    CoffeeSaleForm, TransactionForm, AssessmentForm
)

# ========== UTILITY FUNCTIONS ==========
def get_base_context(request, page_title='Default Page Title'):
    return {
        'page_title': page_title,
        'user': request.user
    }

# ========== CUSTOMER VIEWS ==========
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                form = CustomerForm(request.POST, instance=customer)
            except Customer.DoesNotExist:
                messages.error(request, 'Customer not found!')
                return redirect('customer_list')
        else:  # This is a create
            form = CustomerForm(request.POST)
        
        if form.is_valid():
            customer = form.save(commit=False)
            if not customer_id:
                customer.created_by = request.user
            customer.save()
            messages.success(request, 'Customer saved successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'customers': customers,
    }
    return render(request, 'customer_list.html', context)


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = get_base_context(request, f'Customer Details - {customer.name}')
    
    context.update({
        'customer': customer,
        'milling_processes': customer.milling_processes.all().order_by('-created_at')[:5],
        'transactions': MillingTransaction.objects.filter(
            account__customer=customer
        ).order_by('-created_at')[:5]
    })
    return render(request, 'customer_detail.html', context)

# ========== MILLING PROCESS VIEWS ==========
@login_required
def milling_list(request):
    milling_processes = MillingProcess.objects.select_related('customer').order_by('-created_at')
    form = MillingProcessForm()

    if request.method == 'POST':
        milling_id = request.POST.get('milling_id')
        instance = get_object_or_404(MillingProcess, id=milling_id) if milling_id else None
        
        form = MillingProcessForm(request.POST, instance=instance)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    milling = form.save(commit=False)
                    if not instance:  # Only set created_by for new records
                        milling.created_by = request.user
                    milling.save()
                    messages.success(request, 'Milling process saved successfully!')
                    return redirect('milling_list')
            except Exception as e:
                messages.error(request, f'Error saving process: {str(e)}')
        else:
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return render(request, 'milling_list.html', {
        'form': form,
        'milling_processes': milling_processes
    })

@login_required
def milling_detail(request, pk):
    milling = get_object_or_404(MillingProcess, pk=pk)
    context = get_base_context(request, 'Milling Process Details')
    
    context.update({
        'milling': milling,
        'transactions': milling.transactions.all()
    })
    return render(request, 'milling_detail.html', context)


# ========== SUPPLIER VIEWS ==========
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.order_by('name')
    supplier_id = request.POST.get('supplier_id') if request.method == 'POST' else None
    instance = None

    if supplier_id:
        instance = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=instance, user=request.user)
        if form.is_valid():
            supplier = form.save(commit=False)
            if not instance:
                supplier.created_by = request.user
            supplier.save()
            messages.success(request, f'Supplier {"updated" if instance else "created"} successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm(user=request.user)

    context = {
        'form': form,
        'suppliers': suppliers,
    }
    return render(request, 'supplier_list.html', context)

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    context = get_base_context(request, f'Supplier Details - {supplier.name}')
    
    purchases = supplier.purchases.all().order_by('-purchase_date')[:10]
    context.update({
        'supplier': supplier,
        'purchases': purchases,
        'total_purchases': supplier.purchases.count(),
        'total_quantity': supplier.purchases.aggregate(Sum('quantity'))['quantity__sum'] or 0,
        'total_spent': sum(purchase.total_cost for purchase in purchases)
    })
    return render(request, 'supplier_detail.html', context)

# ========== COFFEE PURCHASE VIEWS ==========
@login_required
def purchase_list(request):
    purchases = CoffeePurchase.objects.select_related('supplier').order_by('-purchase_date')
    instance = None
    action = 'created'

    if request.method == 'POST':
        purchase_id = request.POST.get('purchase_id')
        if purchase_id:
            instance = get_object_or_404(CoffeePurchase, id=purchase_id)
            action = 'updated'

        form = CoffeePurchaseForm(request.POST, instance=instance, user=request.user)

        if form.is_valid():
            try:
                with transaction.atomic():
                    purchase = form.save(commit=False)
                    if not instance:
                        purchase.recorded_by = request.user
                    purchase.save()
                    messages.success(request, f'Purchase {action} successfully!')
                    return redirect('purchase_list')
            except Exception as e:
                messages.error(request, f'Error saving purchase: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CoffeePurchaseForm(user=request.user)

    context = {
        'form': form,
        'purchases': purchases,
        'current_page': 'purchases',
    }
    return render(request, 'purchase_list.html', context)


@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(CoffeePurchase, pk=pk)
    context = get_base_context(request, 'Purchase Details')
    
    context.update({
        'purchase': purchase,
        'assessment': getattr(purchase, 'quality_assessment', None)
    })
    return render(request, 'purchase_detail.html', context)


# ========== COFFEE SALE VIEWS ==========
@login_required
def sale_list(request):
    sales = CoffeeSale.objects.select_related('recorded_by').order_by('-sale_date')
    instance = None
    action = 'created'

    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        if sale_id:
            instance = get_object_or_404(CoffeeSale, id=sale_id)
            action = 'updated'

        form = CoffeeSaleForm(request.POST, instance=instance, user=request.user)

        if form.is_valid():
            try:
                with transaction.atomic():
                    sale = form.save(commit=False)
                    if not instance:
                        sale.recorded_by = request.user
                    sale.save()
                    
                    messages.success(request, f'Sale {action} successfully!')
                    return redirect('sale_list')
            except Exception as e:
                messages.error(request, f'Error saving sale: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CoffeeSaleForm(user=request.user)

    context = {
        'form': form,
        'sales': sales,
        'current_page': 'sales',  # Added for consistent navigation
    }
    return render(request, 'sale_list.html', context)


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(CoffeeSale, pk=pk)
    context = get_base_context(request, 'Sale Details')
    
    context.update({
        'sale': sale
    })
    return render(request, 'sale_detail.html', context)


# ========== INVENTORY VIEWS ==========
@login_required
def inventory_dashboard(request):
    # Get all inventory items
    all_items = CoffeeInventory.objects.select_related().all()
    
    # Basic aggregates
    aggregates = all_items.aggregate(
        total_quantity=Sum('quantity'),
        total_value=Sum('current_value'),
        avg_cost=Avg('average_unit_cost')
    )
    
    # Inventory by category
    inventory_by_category = all_items.values(
        'coffee_category',
        'coffee_type'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum('current_value'),
        average_cost=Avg('average_unit_cost'),
        item_count=Count('id')
    ).order_by('coffee_category', 'coffee_type')
    
    # Calculate percentages for each category
    total_quantity = aggregates['total_quantity'] or 1  # Avoid division by zero
    for category in inventory_by_category:
        category['percentage'] = (category['total_quantity'] / total_quantity) * 100
        category['coffee_category_display'] = dict(CoffeeInventory.COFFEE_CATEGORIES).get(
            category['coffee_category'], 'Unknown'
        )
        category['coffee_type_display'] = dict(CoffeeInventory.COFFEE_TYPE_CHOICES).get(
            category['coffee_type'], 'Unknown'
        )
    
    # Quality assessment summary - modified to avoid using is_rejected as a filter
    quality_summary = Assessment.objects.annotate(
        is_rejected_case=Case(
            When(
                Q(moisture_content__gt=20) | 
                Q(below_screen_12__gt=3) |
                Q(outturn__isnull=True) |
                Q(outturn=0),
                then=Value(1)
            ),
            default=Value(0),
            output_field=IntegerField()
        )
    ).values(
        'coffee__coffee_category',
        'coffee__coffee_type'
    ).annotate(
        total_assessed=Count('id'),
        avg_moisture=Avg('moisture_content'),
        avg_outturn=Avg('outturn'),
        rejected_count=Sum('is_rejected_case')
    ).order_by('coffee__coffee_category', 'coffee__coffee_type')
    
    # Stock status breakdown
    stock_status = {
        'low': all_items.filter(quantity__lt=10).count(),
        'medium': all_items.filter(quantity__gte=10, quantity__lt=50).count(),
        'high': all_items.filter(quantity__gte=50).count()
    }
    
    # Recent purchases (last 30 days)
    recent_purchases = CoffeePurchase.objects.filter(
        purchase_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).select_related('supplier').order_by('-purchase_date')[:5]
    
    context = {
        'page_title': 'Inventory Dashboard',
        'inventory_items': all_items,
        'total_items': all_items.count(),
        'total_quantity': aggregates['total_quantity'] or 0,
        'total_value': aggregates['total_value'] or 0,
        'average_cost_per_kg': aggregates['avg_cost'] or 0,
        'inventory_by_category': inventory_by_category,
        'quality_summary': quality_summary,
        'stock_status': stock_status,
        'recent_purchases': recent_purchases,
        'low_stock_items': all_items.filter(quantity__lt=10),
    }
    return render(request, 'inventory_dashboard.html', context)



@login_required
def inventory_detail(request, pk):
    inventory = get_object_or_404(CoffeeInventory, pk=pk)
    context = get_base_context(request, 'Inventory Details')
    
    context.update({
        'inventory': inventory,
        'purchases': CoffeePurchase.objects.filter(
            coffee_type=inventory.coffee_type
        ).order_by('-purchase_date')[:10],
        'sales': CoffeeSale.objects.filter(
            coffee_type=inventory.coffee_type
        ).order_by('-sale_date')[:10]
    })
    return render(request, 'inventory_detail.html', context)

# ========== DASHBOARD VIEW ==========
@login_required
def dashboard(request):
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    context = get_base_context(request, 'Dashboard')
    context.update({
        'total_customers': Customer.objects.count(),
        'new_customers_week': Customer.objects.filter(created_at__date__gte=last_week).count(),
        'pending_milling': MillingProcess.objects.filter(status='P').count(),
        'completed_milling': MillingProcess.objects.filter(status='C').count(),
        'total_hulled': MillingProcess.objects.filter(status='C').aggregate(Sum('hulled_weight'))['hulled_weight__sum'] or 0,
        'total_revenue': MillingTransaction.objects.filter(transaction_type='C').aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_debits': MillingTransaction.objects.filter(transaction_type='D').aggregate(Sum('amount'))['amount__sum'] or 0,
        'top_customers': Customer.objects.annotate(
            milling_volume=Sum('milling_processes__hulled_weight')
        ).exclude(milling_volume=None).order_by('-milling_volume')[:5],
        'recent_transactions': MillingTransaction.objects.select_related('account__customer').order_by('-created_at')[:5],
        'recent_sales': CoffeeSale.objects.select_related('recorded_by').order_by('-sale_date')[:5],
    })
    return render(request, 'index.html', context)

@login_required
def customer_search(request):
    search_term = request.GET.get('q', '').strip()
    if not search_term:
        return JsonResponse({'error': 'No search term provided'}, status=400)
    
    customers = Customer.objects.filter(
        Q(name__icontains=search_term) | Q(phone__icontains=search_term)
    ).order_by('name')[:10]
    
    results = [{
        'id': customer.id,
        'text': f"{customer.name} ({customer.phone})",
        'name': customer.name,
        'phone': customer.phone
    } for customer in customers]
    
    return JsonResponse({'results': results})


# ==============TRANSACTION VIEWS ==============
@login_required
def transaction_list(request):
    transactions = MillingTransaction.objects.all().order_by('-created_at')
    instance = None
    action = 'created'

    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        if transaction_id:
            instance = get_object_or_404(MillingTransaction, id=transaction_id)
            action = 'updated'

        form = TransactionForm(request.POST, instance=instance)

        if form.is_valid():
            transaction = form.save(commit=False)
            if not instance:
                transaction.created_by = request.user
            transaction.save()
            messages.success(request, f'Transaction {action} successfully!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TransactionForm()

    context = {
        'form': form,
        'transactions': transactions,
    }
    return render(request, 'transaction_list.html', context)


@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(MillingTransaction, pk=pk)
    context = get_base_context(request, 'Transaction Details')
    
    context.update({
        'transaction': transaction
    })
    return render(request, 'transaction_detail.html', context)



# ========== ASSESSMENT VIEWS ==========
@login_required
def assessment_list(request):
    # Get all assessments with related data
    assessments = Assessment.objects.select_related(
        'coffee', 
        'coffee__supplier',
        'assessed_by'
    ).order_by('-coffee__purchase_date')
    
    # Get purchases needing assessment
    unassessed_purchases = CoffeePurchase.objects.filter(
        quality_assessment__isnull=True
    ).select_related('supplier').order_by('-purchase_date')
    
    # Calculate metrics for the stats cards
    completed_this_month = assessments.filter(
        coffee__purchase_date__month=timezone.now().month,
        coffee__purchase_date__year=timezone.now().year
    ).count()
    
    # Calculate rejection rate (percentage of rejected assessments)
    total_assessments = assessments.count()
    rejected_count = assessments.filter(
        Q(below_screen_12__gt=3) | 
        Q(outturn__isnull=True) | 
        Q(outturn=0)
    ).count()
    
    rejection_rate = round((rejected_count / total_assessments) * 100, 1) if total_assessments > 0 else 0
    
    # Pagination
    paginator = Paginator(assessments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add price analysis properties to each assessment in the page
    for assessment in page_obj:
        assessment.price_difference_percentage = 0
        if not assessment.is_rejected and assessment.final_price and assessment.coffee.reference_price:
            difference = float(assessment.final_price) - float(assessment.coffee.reference_price)
            assessment.price_difference_percentage = (difference / float(assessment.coffee.reference_price)) * 100
    
    return render(request, 'assessment_list.html', {
        'assessments': page_obj,
        'unassessed_purchases': unassessed_purchases,
        'completed_this_month': completed_this_month,
        'rejection_rate': rejection_rate,
        'page_obj': page_obj,  # For pagination controls
    })




@login_required
def assessment_create(request, pk):
    coffee_purchase = get_object_or_404(CoffeePurchase, pk=pk)

    try:
        # Try to get existing assessment
        assessment = coffee_purchase.quality_assessment
    except Assessment.DoesNotExist:
        assessment = None

    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            new_assessment = form.save(commit=False)
            new_assessment.coffee = coffee_purchase
            new_assessment.assessed_by = request.user
            new_assessment.save()

            # Mark purchase as assessed
            coffee_purchase.assessment = True
            coffee_purchase.save(update_fields=['assessment'])

            messages.success(request, 'Quality assessment created successfully!')
            return redirect('assessment_list')
    else:
        form = AssessmentForm(instance=assessment)

    context = {
        'form': form,
        'coffee_purchase': coffee_purchase,
        'page_title': f'Create Assessment for {coffee_purchase}',
    }
    return render(request, 'assessment_form.html', context)

@login_required
def assessment_detail(request, pk):
    """
    Detailed view of a single quality assessment
    """
    assessment = get_object_or_404(
        Assessment.objects.select_related('coffee', 'coffee__supplier'),
        pk=pk
    )
    
    context = {
        'assessment': assessment,
        'page_title': f'Assessment - {assessment.coffee}',
    }
    return render(request, 'assessment_detail.html', context)


@login_required
def coffee_purchase_json(request, pk):
    try:
        purchase = CoffeePurchase.objects.select_related('supplier').get(pk=pk)
        data = {
            'coffee_type_display': purchase.get_coffee_type_display(),
            'coffee_category_display': purchase.get_coffee_category_display(),
            'supplier_name': purchase.supplier.name,
            'quantity': purchase.quantity,
            'purchase_date': purchase.purchase_date.isoformat(),
            'reference_price': purchase.reference_price,
        }
        return JsonResponse(data)
    except CoffeePurchase.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)