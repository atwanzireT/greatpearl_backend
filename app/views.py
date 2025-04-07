from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Sum
from django.conf import settings
from .models import Customer, CoffeeMilling, Payment, Notification
from .forms import CustomerForm, CoffeeMillingForm, PaymentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError

@login_required
def index(request):
    customer_count = Customer.objects.count()
    hulked_coffee_count = CoffeeMilling.objects.aggregate(total_hulked=Sum('hulled_coffee_weight'))['total_hulked'] or 0
    total_revenue_count = CoffeeMilling.objects.aggregate(total_revenue=Sum('total_cost'))['total_revenue'] or 0
    customers = Customer.objects.order_by('-id')[:10]

    # Get the top 5 customers by the amount of coffee they brought for milling
    top_customers = CoffeeMilling.objects.values('customer__name').annotate(
        total_coffee=Sum('raw_coffee_weight')
    ).order_by('-total_coffee')[:5]

    # Calculate total paid money and debts
    total_paid = Payment.objects.aggregate(total_paid=Sum('amount_paid'))['total_paid'] or 0
    total_debts = (CoffeeMilling.objects.aggregate(total_debts=Sum('total_cost'))['total_debts'] or 0) - total_paid
    
    # Get the authenticated user's profile picture
    user = request.user
    profile_picture = "/static/assets/images/default.jpg"
    if hasattr(user, 'profile') and hasattr(user.profile, 'profile_picture') and user.profile.profile_picture:
        profile_picture = user.profile.profile_picture.url

    # Pass data to the template
    context = {
        "customers": customers,
        "customer_count": customer_count,
        "hulked_coffee_count": hulked_coffee_count,
        "total_revenue_count": total_revenue_count,
        "top_customers": top_customers,
        "total_paid": total_paid,
        "total_debts": total_debts,
        "profile_picture": profile_picture,
    }

    return render(request, "index.html", context)

# -------------------- CUSTOMER VIEWS --------------------

class CustomerListView(LoginRequiredMixin, ListView):
    """
    Displays a list of all registered customers.
    """
    model = Customer
    template_name = "customer_list.html"
    context_object_name = "customers"
    paginate_by = 20

class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    Shows details of a single customer.
    """
    model = Customer
    template_name = "customer_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        context['millings'] = CoffeeMilling.objects.filter(customer=customer)
        context['payments'] = Payment.objects.filter(customer=customer)
        context['notifications'] = Notification.objects.filter(customer=customer)
        return context

class CustomerCreateView(LoginRequiredMixin, CreateView):
    """
    Registers a new customer.
    """
    model = Customer
    form_class = CustomerForm
    template_name = "customer_form.html"
    success_url = reverse_lazy("customer_list")
    
    def form_valid(self, form):
        form.instance.registered_by = self.request.user 
        return super().form_valid(form)

# -------------------- MILLING VIEWS --------------------

class MillingListView(LoginRequiredMixin, ListView):
    """
    Displays all coffee milling transactions.
    """
    model = CoffeeMilling
    template_name = "milling_list.html"
    context_object_name = "millings"
    paginate_by = 20

class MillingCreateView(LoginRequiredMixin, CreateView):
    """
    Handles recording of new coffee milling.
    """
    model = CoffeeMilling
    form_class = CoffeeMillingForm
    template_name = "milling_form.html"
    success_url = reverse_lazy("milling_list")

    def form_valid(self, form):
        """
        Custom form valid method to calculate milling costs and create a notification.
        """
        try:
            milling = form.save(commit=False)

            # Ensure positive and valid values for weight fields and cost_per_kg
            self._validate_milling_data(milling)

            # Assign the user who registered the milling
            milling.registered_by = self.request.user

            # Save the milling instance - total_cost is calculated in the model's save method
            with transaction.atomic():  # Ensure atomicity for database integrity
                milling.save()

                # Create a notification for the customer
                self._create_notification(milling)

            return super().form_valid(form)

        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
    def _validate_milling_data(self, milling):
        """
        Validates that milling data is correct.
        """
        if milling.raw_coffee_weight <= 0:
            raise ValidationError("Raw coffee weight must be greater than zero.")
        if milling.hulled_coffee_weight <= 0:
            raise ValidationError("Hulled coffee weight must be greater than zero.")
        if milling.cost_per_kg <= 0:
            raise ValidationError("Cost per kg must be greater than zero.")
        if milling.hulled_coffee_weight > milling.raw_coffee_weight:
            raise ValidationError("Hulled coffee weight cannot be greater than raw coffee weight.")

    def _create_notification(self, milling):
        """
        Creates a notification for the customer regarding the milling.
        """
        Notification.objects.create(
            customer=milling.customer,
            message=f"Coffee of {milling.raw_coffee_weight} Kg was milled. Total cost: {milling.total_cost}.",
            notification_type="milling_completion"
        )

# -------------------- PAYMENT VIEWS --------------------

class PaymentListView(LoginRequiredMixin, ListView):
    """
    Displays all payment transactions.
    """
    model = Payment
    template_name = "payment_list.html"
    context_object_name = "payments"
    paginate_by = 20
    
class PaymentCreateView(LoginRequiredMixin, CreateView):
    """
    Handles payment for coffee milling.
    """
    model = Payment
    form_class = PaymentForm
    template_name = "payment_form.html"
    success_url = reverse_lazy("payment_list")

    def get_initial(self):
        """Pre-fill form with milling data if available"""
        initial = super().get_initial()
        if 'milling_id' in self.kwargs:
            milling = get_object_or_404(CoffeeMilling, id=self.kwargs['milling_id'])
            initial['milling_record'] = milling
            initial['customer'] = milling.customer
            initial['amount_paid'] = milling.total_cost
        return initial

    def form_valid(self, form):
        payment = form.save(commit=False)
        payment.registered_by = self.request.user
        payment.save()

        # Create a notification for the payment
        Notification.objects.create(
            customer=payment.customer,
            message=f"Payment of {payment.amount_paid} received for your milled coffee.",
            notification_type="payment_reminder"
        )

        return super().form_valid(form)
    
class NotificationListView(LoginRequiredMixin, ListView):
    """
    Displays all notifications for a specific customer.
    """
    model = Notification
    template_name = "notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        customer_id = self.kwargs.get("customer_id")
        queryset = Notification.objects.order_by("-created_at")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset