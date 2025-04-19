from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import re
from django.db import transaction
import random
from django.conf import settings 
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class Customer(models.Model):
    registration_number = models.CharField(max_length=50, unique=True, editable=False, help_text=_("Auto-generated customer ID (format: GPC001)"))
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    registered_at = models.DateTimeField(default=timezone.now)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="registered_customers")

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Enhanced auto-generation of registration number with better concurrency handling."""
        if not self.registration_number:
            with transaction.atomic():
                last_customer = Customer.objects.select_for_update(skip_locked=True, of=('self',)).order_by("-id").first()
                try:
                    new_number = int(last_customer.registration_number[3:]) + 1 if (last_customer and last_customer.registration_number.startswith("GPC")) else 1
                    self.registration_number = f"GPC{new_number:03d}"
                except (ValueError, IndexError, TypeError):
                    self.registration_number = f"GPC{random.randint(1, 999):03d}"
        super().save(*args, **kwargs)

class CoffeeMilling(models.Model):
    """Improved coffee milling transaction model with additional fields and validation."""

    COFFEE_TYPE_CHOICES = [
        ('arabica', 'Arabica'), 
        ('robusta', 'Robusta')
    ]
    MILLING_STATUS_CHOICES = [
        ('pending', 'Pending'), 
        ('completed', 'Completed'), 
        ('cancelled', 'Cancelled')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="milling_records", help_text=_("Customer who brought the coffee"))
    hulled_coffee_weight = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(0.01)], 
        help_text=_("Weight of coffee after milling (Kg)")
    )

    milling_date = models.DateTimeField(default=timezone.now, help_text=_("Date and time when milling occurred"))
    cost_per_kg = models.DecimalField(
        max_digits=8, decimal_places=2, 
        validators=[MinValueValidator(0.01), MaxValueValidator(1000)], 
        help_text=_("Cost per Kg for milling")
    )
    total_cost = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False, 
        help_text=_("Auto-calculated total milling cost")
    )
    milling_status = models.CharField(
        max_length=20, choices=MILLING_STATUS_CHOICES, default='pending', 
        help_text=_("Current status of the milling process")
    )
    notes = models.TextField(blank=True, null=True, help_text=_("Additional notes about this milling"))
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="milling", 
        help_text=_("Staff member who recorded this milling")
    )
    registered_at = models.DateTimeField(default=timezone.now, help_text=_("Date and time when record was created"))

    def save(self, *args, **kwargs):
        """Calculate total cost before saving."""
        self.total_cost = round(self.hulled_coffee_weight * self.cost_per_kg, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.name} - {self.raw_coffee_weight}kg"

class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    milling_record = models.ForeignKey(CoffeeMilling, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(default=timezone.now)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="registered_payments")

    def __str__(self):
        return f"Payment of {self.amount_paid} by {self.customer.name}"


class Notification(models.Model):
    """
    Sends notifications to customers about their transactions.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('payment_reminder', 'Payment Reminder'),
        ('milling_completion', 'Milling Completion'),
        ('general', 'General'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.customer.name}"