from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db import transaction
import re
from decimal import Decimal


class Customer(models.Model):
    """Customer model with auto-generated ID"""
    id = models.CharField(primary_key=True, max_length=6, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.id})"

    def save(self, *args, **kwargs):
        if not self.id:
            prefix = 'GPC-CUS'
            last = Customer.objects.filter(id__startswith=prefix).order_by('id').last()
            if last:
                new_num = int(last.id[len(prefix):]) + 1
            else:
                new_num = 1
            self.id = f"{prefix}{new_num:03d}"
        super().save(*args, **kwargs)

class MillingProcess(models.Model):
    """Tracks coffee milling processes"""
    PENDING = 'P'
    COMPLETED = 'C'
    CANCELLED = 'X'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='milling_processes')
    initial_weight = models.DecimalField(max_digits=6, blank=True, null=True, decimal_places=2, validators=[MinValueValidator(0.1)])
    hulled_weight = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.1)], null=True, blank=True)
    milling_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null = True, default=150.00)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, blank=True, null = True, default=COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    notes = models.TextField(blank=True)

    @property
    def milling_cost(self):
        if self.hulled_weight is None or self.milling_rate is None:
            return Decimal('0.00')
        return Decimal(str(self.hulled_weight)) * Decimal(str(self.milling_rate))

    def save(self, *args, **kwargs):
        if self.status == self.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.id} {self.customer.name} - Ugx {self.milling_cost}"

class CustomerAccount(models.Model):
    """Tracks customer balances"""
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='account')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def update_balance(self, amount):
        """Update account balance"""
        self.balance += amount
        self.save()

    def __str__(self):
        return f"Account for {self.customer.name} (Balance: {self.balance})"

class MillingTransaction(models.Model):
    """Records all financial transactions"""
    DEBIT = 'D'
    CREDIT = 'C'
    TYPE_CHOICES = [
        (DEBIT, 'Debit'),
        (CREDIT, 'Credit'),
    ]

    account = models.ForeignKey(CustomerAccount, on_delete=models.PROTECT, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    reference = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    milling_process = models.ForeignKey(
        MillingProcess, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount}"


class Supplier(models.Model):
    """Track coffee suppliers/vendors"""
    id = models.CharField(primary_key=True, max_length=8, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Coffee Supplier"
        verbose_name_plural = "Coffee Suppliers"

    def __str__(self):
        return f"{self.name} ({self.id})"

  
    def save(self, *args, **kwargs):
        if not self.id:
            prefix = 'GPC-SUP'
            last = Supplier.objects.filter(id__startswith=prefix).order_by('id').last()
            if last:
                # Extract the numeric part after the prefix
                match = re.search(rf'^{prefix}(\d+)$', last.id)
                if match:
                    new_num = int(match.group(1)) + 1
                else:
                    new_num = 1
            else:
                new_num = 1
            self.id = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)


class CoffeePurchase(models.Model):
    """Records coffee purchases from suppliers with detailed classification"""
    # Coffee Categories
    GREEN = 'GR'
    PARCHMENT = 'PA'
    KIBOKO = 'KB'
    COFFEE_CATEGORIES = [
        (GREEN, 'Green Coffee'),
        (PARCHMENT, 'Parchment Coffee'),
        (KIBOKO, 'Kiboko Coffee'),
    ]
    
    # Coffee Types
    ARABICA = 'AR'
    ROBUSTA = 'RB'
    COFFEE_TYPES = [
        (ARABICA, 'Arabica'),
        (ROBUSTA, 'Robusta'),
    ]

    PAYMENT_PENDING = 'P'
    PAYMENT_PAID = 'D'
    PAYMENT_PARTIAL = 'T'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_PARTIAL, 'Partial'),
    ]


    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    coffee_category = models.CharField(
        max_length=2, choices=COFFEE_CATEGORIES, verbose_name="Coffee Form", blank=True
    )
    coffee_type = models.CharField(max_length=2, choices=COFFEE_TYPES, default="AR")
    quantity = models.DecimalField(
        max_digits=8, decimal_places=0, validators=[MinValueValidator(0.01)], help_text="Weight in kilograms"
    )
    bags = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)], help_text="Number of bags (if applicable)"
    )
    reference_price = models.DecimalField(
        max_digits=8, decimal_places=0, default=0, validators=[MinValueValidator(0.01)], help_text="Reference price per kilogram"
    )
    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING, verbose_name="Payment Status"
    )
    assessment = models.BooleanField(default=False, verbose_name="Quality Assessment")
    purchase_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False
    )


    @property
    def total_cost(self):
        """Calculate total cost with null checks"""
        if self.quantity is None or self.reference_price is None:
            return 0.00
        return round(float(self.quantity) * float(self.reference_price), 2)

    class Meta:
        ordering = ['-purchase_date']
        verbose_name = "Coffee Purchase"
        verbose_name_plural = "Coffee Purchases"
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0.01),
                name="quantity_gte_001"
            ),
        ]

    def save(self, *args, **kwargs):
        """Auto-set recorded_by if not set"""
        if not self.pk and not self.recorded_by_id:
            self.recorded_by = getattr(self, 'request_user', None)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_coffee_category_display()} {self.get_coffee_type_display()} - {self.quantity}kg"
    

class Assessment(models.Model):
    coffee = models.OneToOneField('CoffeePurchase', on_delete=models.PROTECT, related_name='quality_assessment')
    moisture_content = models.FloatField(blank=True, null=True)
    group1_defects = models.FloatField(blank=True, null=True)
    group2_defects = models.FloatField(blank=True, null=True)
    below_screen_12 = models.FloatField(blank=True, null=True)
    outturn = models.FloatField(blank=True, null=True)
    pods = models.FloatField(blank=True, null=True)
    husks = models.FloatField(blank=True, null=True)
    stones = models.FloatField(blank=True, null=True)
    fm = models.FloatField(blank=True, null=True)
    discretion = models.FloatField(default=0)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
        related_name='assessments', null=True, blank=True
    )

    @property
    def actual_outturn(self):
        """
        Computes actual outturn based on a formula or external reference.
        Placeholder formula here, adjust to match business logic.
        """
        # ⚠️ Replace with your real logic. This is a placeholder.
        if self.moisture_content is None:
            return None
        
        # Example: actual_outturn = 100 - (group1_defects + group2_defects + moisture effect)
        g1 = self.group1_defects or 0
        g2 = self.group2_defects or 0
        mc = self.moisture_content or 0
        return max(100 - (g1 + g2 + mc), 0)

    @property
    def is_rejected(self):
        """
        Reject if:
        - outturn or actual_outturn is missing
        - below_screen_12 exceeds 3%
        """
        if self.below_screen_12 is not None and self.below_screen_12 > 3:
            return True
        if self.outturn in [None, 0] or self.actual_outturn is None:
            return True
        return False

    @property
    def outturn_price(self):
        if self.is_rejected:
            return None
        ref_price = float(self.coffee.reference_price or 0)
        return (self.actual_outturn / self.outturn) * ref_price

    @property
    def foreign_matter_penalty(self):
        fm_total = sum([
            self.pods or 0,
            self.husks or 0,
            self.stones or 0
        ])
        penalty_rate = 146.55
        return fm_total * penalty_rate

    @property
    def final_price(self):
        if self.is_rejected:
            return "REJECT"

        base_price = self.outturn_price or 0
        penalty = self.foreign_matter_penalty
        adjusted = base_price - penalty + (self.discretion or 0)

        return round(max(adjusted, 0), 2)

    def __str__(self):
        return f"Assessment for {self.coffee} - Final Price: {self.final_price}"


class CoffeeSale(models.Model):
     # Coffee Categories
    GREEN = 'GR'
    PARCHMENT = 'PA'
    KIBOKO = 'KB'
    COFFEE_CATEGORIES = [
        (GREEN, 'Green Coffee'),
        (PARCHMENT, 'Parchment Coffee'),
        (KIBOKO, 'Kiboko Coffee'),
    ]
    
    # Coffee Types
    ARABICA = 'AR'
    ROBUSTA = 'RB'
    COFFEE_TYPES = [
        (ARABICA, 'Arabica'),
        (ROBUSTA, 'Robusta'),
    ]
    customer = models.CharField(blank=True, null=True, max_length=250)
    customer_address = models.CharField(blank=True, null=True, max_length=150)
    customer_contact = models.CharField(blank=True, null=True, max_length=150)
    coffee_category = models.CharField(
        max_length=2, choices=COFFEE_CATEGORIES, verbose_name="Coffee Form", blank=True
    )
    coffee_type = models.CharField(max_length=2, choices=COFFEE_TYPES, default="AR")
    quantity = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    sale_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    @property
    def total_amount(self):
        return self.quantity * self.unit_price

    class Meta:
        ordering = ['-sale_date']
        verbose_name = "Coffee Sale"
        verbose_name_plural = "Coffee Sales"

    def __str__(self):
        return f"Sale #{self.id} - {self.coffee_type}"


class CoffeeInventory(models.Model):
    # Coffee Categories (same as in CoffeePurchase and CoffeeSale)
    GREEN = 'GR'
    PARCHMENT = 'PA'
    KIBOKO = 'KB'
    COFFEE_CATEGORIES = [
        (GREEN, 'Green Coffee'),
        (PARCHMENT, 'Parchment Coffee'),
        (KIBOKO, 'Kiboko Coffee'),
    ]

    # Coffee Types
    COFFEE_TYPE_CHOICES = [
        ('ARABICA', 'Arabica'),
        ('ROBUSTA', 'Robusta'),
        ('BLEND', 'Blend'),
    ]

    coffee_category = models.CharField(
        max_length=2,
        choices=COFFEE_CATEGORIES,
        verbose_name="Coffee Form",
        blank=True
    )
    coffee_type = models.CharField(max_length=20, choices=COFFEE_TYPE_CHOICES, default='ARABICA')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, default='kg')
    last_updated = models.DateTimeField(auto_now=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name_plural = 'Coffee Inventory'
        unique_together = ['coffee_category', 'coffee_type']  # Updated to include coffee_category
        ordering = ['coffee_category', 'coffee_type']  # Updated ordering

    def __str__(self):
        category_display = dict(self.COFFEE_CATEGORIES).get(self.coffee_category, 'Unknown')
        return f"{category_display} {self.get_coffee_type_display()} - {self.quantity}{self.unit}"

    def has_sufficient_stock(self, quantity):
        """Check if sufficient stock exists"""
        return self.quantity >= Decimal(str(quantity))

    def update_inventory(self, quantity_change, cost_change=0):
        """Update inventory levels and calculate new average cost"""
        new_quantity = self.quantity + Decimal(str(quantity_change))

        if new_quantity < 0:
            raise ValueError(
                f"Insufficient stock. Available: {self.quantity}{self.unit}, Requested: {-quantity_change}{self.unit}")

        # Calculate new average cost (only for purchases)
        if quantity_change > 0:  # Purchase
            if self.quantity <= 0:
                new_avg_cost = Decimal(str(cost_change)) / Decimal(str(quantity_change))
            else:
                total_cost = (self.quantity * self.average_unit_cost) + Decimal(str(cost_change))
                new_avg_cost = total_cost / (self.quantity + Decimal(str(quantity_change)))
        else:  # Sale - maintain current average cost
            new_avg_cost = self.average_unit_cost

        self.quantity = new_quantity
        self.average_unit_cost = new_avg_cost
        self.current_value = self.quantity * self.average_unit_cost
        self.save()