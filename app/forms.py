from django import forms
from django_select2 import forms as s2forms
from .models import (
    Customer, MillingProcess, CustomerAccount, MillingTransaction,
    Supplier, CoffeePurchase, CoffeeSale, Assessment, CoffeeInventory
)
from django.core.exceptions import ValidationError

# ========== CUSTOM WIDGETS ==========
class BaseSelect2Widget(s2forms.ModelSelect2Widget):
    """Base Select2 widget with consistent styling"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ease-in-out bg-white shadow-sm hover:shadow-md',
            'data-placeholder': self.get_placeholder(),
            'data-allow-clear': 'true'
        })

    def get_placeholder(self):
        return "Search or select..."

class CustomerWidget(BaseSelect2Widget):
    search_fields = ["name__icontains", "phone__icontains", "id__icontains"]
    def get_placeholder(self):
        return "Search customer by name, phone or ID..."

class SupplierWidget(BaseSelect2Widget):
    search_fields = ["name__icontains", "phone__icontains", "id__icontains"]
    def get_placeholder(self):
        return "Search supplier by name, phone or ID..."

class CustomerAccountWidget(BaseSelect2Widget):
    search_fields = ["customer__name__icontains", "customer__phone__icontains"]
    def get_placeholder(self):
        return "Search by customer name or phone..."

class MillingProcessWidget(BaseSelect2Widget):
    search_fields = ["customer__name__icontains", "id__icontains"]
    def get_placeholder(self):
        return "Search milling process by customer or ID..."

class CoffeeInventoryWidget(BaseSelect2Widget):
    search_fields = ["coffee_type__icontains", "coffee_category__icontains"]
    def get_placeholder(self):
        return "Search inventory by coffee type or category..."

# ========== FORM MIXINS ==========
class EnhancedTailwindFormMixin:
    """Enhanced form mixin with modern Tailwind CSS styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_styling()
        self.setup_fields()
    
    def apply_tailwind_styling(self):
        """Apply consistent Tailwind CSS styling to all form fields"""
        for field_name, field in self.fields.items():
            # Skip Select2 widgets as they have their own styling
            if isinstance(field.widget, (s2forms.Select2Widget, s2forms.Select2MultipleWidget)):
                continue
            
            # Base classes for all inputs
            base_classes = (
                'w-full px-4 py-3 border rounded-lg transition-all duration-200 ease-in-out '
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'bg-white shadow-sm hover:shadow-md placeholder-gray-400'
            )
            
            # Error state styling
            if field_name in self.errors:
                base_classes += ' border-red-500 focus:ring-red-500 focus:border-red-500 bg-red-50'
            else:
                base_classes += ' border-gray-300'
            
            # Required field styling
            if field.required:
                base_classes += ' ring-1 ring-blue-100'
            
            # Widget-specific styling
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': (
                        'h-5 w-5 text-blue-600 bg-white border-gray-300 rounded '
                        'focus:ring-blue-500 focus:ring-2 transition-all duration-200 '
                        'hover:bg-blue-50 cursor-pointer'
                    )
                })
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({
                    'class': 'text-blue-600 bg-white border-gray-300 focus:ring-blue-500'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': f'{base_classes} pr-10 cursor-pointer appearance-none'
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': f'{base_classes} resize-none min-h-[100px]',
                    'rows': field.widget.attrs.get('rows', 4)
                })
            elif isinstance(field.widget, (forms.DateInput, forms.DateTimeInput)):
                field.widget.attrs.update({
                    'class': f'{base_classes} cursor-pointer',
                    'autocomplete': 'off'
                })
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.update({
                    'class': f'{base_classes} text-right font-mono',
                    'autocomplete': 'off'
                })
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    'class': (
                        'w-full px-4 py-3 border border-gray-300 rounded-lg '
                        'file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
                        'file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 '
                        'hover:file:bg-blue-100 file:cursor-pointer cursor-pointer'
                    )
                })
            else:
                field.widget.attrs.update({
                    'class': f'{base_classes}',
                    'autocomplete': 'off'
                })
    
    def setup_fields(self):
        """Setup field-specific attributes and help texts"""
        pass

# ========== MODEL FORMS ==========
class CustomerForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full legal name'}),
            'phone': forms.TextInput(attrs={'placeholder': '+256XXXXXXXXX'}),
        }
    
    def setup_fields(self):
        self.fields['name'].help_text = "Customer's full legal name"
        self.fields['phone'].help_text = "Unique phone number with country code"

class MillingProcessForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = MillingProcess
        fields = ['customer', 'initial_weight', 'hulled_weight', 'milling_rate', 'status', 'notes']
        widgets = {
            'customer': CustomerWidget,
            'initial_weight': forms.NumberInput(attrs={'step': '0.01', 'min': '0.1'}),
            'hulled_weight': forms.NumberInput(attrs={'step': '0.01', 'min': '0.1'}),
            'milling_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def setup_fields(self):
        self.fields['initial_weight'].help_text = "Weight before milling (kg)"
        self.fields['hulled_weight'].help_text = "Weight after milling (kg)"
        self.fields['milling_rate'].help_text = "Rate per kg (UGX)"
        self.fields['notes'].help_text = "Optional process notes"

class CustomerAccountForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = CustomerAccount
        fields = ['customer', 'balance']
        widgets = {
            'customer': CustomerWidget,
            'balance': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def setup_fields(self):
        self.fields['balance'].help_text = "Initial account balance in UGX"

class TransactionForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = MillingTransaction
        fields = ['account', 'amount', 'transaction_type', 'reference', 'milling_process']
        widgets = {
            'account': CustomerAccountWidget,
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'reference': forms.TextInput(attrs={'maxlength': '50'}),
            'milling_process': MillingProcessWidget,
        }
    
    def setup_fields(self):
        self.fields['transaction_type'].initial = MillingTransaction.CREDIT
        self.fields['amount'].help_text = "Transaction amount in UGX"
        self.fields['reference'].help_text = "Optional reference number"

class SupplierForm(EnhancedTailwindFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': '255'}),
            'phone': forms.TextInput(attrs={'maxlength': '20'}),
            'email': forms.EmailInput(),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def setup_fields(self):
        self.fields['name'].help_text = "Official supplier/company name"
        self.fields['phone'].help_text = "Primary contact number"
        self.fields['email'].help_text = "Business email address"
        self.fields['address'].help_text = "Physical address details"

class CoffeePurchaseForm(EnhancedTailwindFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        
    class Meta:
        model = CoffeePurchase
        fields = [
            'supplier', 'coffee_category', 'coffee_type', 'quantity', 'bags',
            'reference_price', 'payment_status', 'assessment', 'purchase_date',
            'delivery_date', 'notes'
        ]
        widgets = {
            'supplier': SupplierWidget,
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def setup_fields(self):
        self.fields['quantity'].widget.attrs.update({
            'step': '0.01',
            'min': '0.01'
        })
        self.fields['bags'].widget.attrs.update({
            'min': '0'
        })
        self.fields['reference_price'].widget.attrs.update({
            'step': '0.01',
            'min': '0.01'
        })
        
        self.fields['quantity'].help_text = "Weight in kilograms"
        self.fields['bags'].help_text = "Number of bags (if applicable)"
        self.fields['reference_price'].help_text = "Reference price per kilogram (UGX)"
        self.fields['assessment'].help_text = "Check if quality assessment was done"
        self.fields['purchase_date'].help_text = "Date when the purchase was recorded"
        self.fields['delivery_date'].help_text = "Date coffee was delivered (optional)"
        self.fields['notes'].help_text = "Additional notes or remarks"

        # Set initial values
        self.fields['coffee_type'].initial = CoffeePurchase.ARABICA
        self.fields['payment_status'].initial = CoffeePurchase.PAYMENT_PENDING

class AssessmentForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Assessment
        fields = [
            'coffee', 'moisture_content', 'group1_defects', 'group2_defects',
            'below_screen_12', 'outturn', 'pods', 'husks',
            'stones', 'fm', 'discretion'
        ]
        widgets = {
            'coffee': forms.Select(attrs={'class': 'hidden'}),
        }
        labels = {
            'moisture_content': 'Moisture Content (%)',
            'group1_defects': 'Group 1 Defects',
            'group2_defects': 'Group 2 Defects',
            'below_screen_12': 'Below Screen 12',
            'outturn': 'Outturn',
            'pods': 'Pods',
            'husks': 'Husks',
            'stones': 'Stones',
            'fm': 'Foreign Matter (FM)',
            'discretion': 'Discretion Adjustment',
        }
        help_texts = {
            'moisture_content': 'Enter moisture content percentage (0-20%)',
            'fm': 'Total foreign matter content',
            'discretion': 'Can be positive or negative to adjust final price',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add specific attributes that weren't covered by the mixin
        self.fields['moisture_content'].widget.attrs.update({
            'step': '0.1',
            'min': '0',
            'max': '20',
        })
        
        # Set number inputs to have right-aligned text
        for field in ['group1_defects', 'group2_defects', 'below_screen_12', 
                     'outturn', 'pods', 'husks', 'stones', 'fm', 'discretion']:
            self.fields[field].widget.attrs.update({
                'step': '0.1',
                'min': '0',
                'class': self.fields[field].widget.attrs.get('class', '') + ' text-right'
            })

    def clean(self):
        cleaned_data = super().clean()
        moisture = cleaned_data.get('moisture_content')
        
        if moisture is not None and (moisture < 0 or moisture > 20):
            self.add_error('moisture_content', "Moisture content must be between 0 and 20%")
            
        return cleaned_data

class CoffeeSaleForm(EnhancedTailwindFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

    class Meta:
        model = CoffeeSale
        fields = [
            'customer', 'customer_address', 'customer_contact',
            'coffee_category', 'coffee_type', 'quantity', 'unit_price',
            'sale_date', 'notes'
        ]
        widgets = {
            'customer': forms.TextInput(attrs={'maxlength': '255'}),
            'customer_address': forms.TextInput(attrs={'maxlength': '150'}),
            'customer_contact': forms.TextInput(attrs={'maxlength': '150'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def setup_fields(self):
        self.fields['quantity'].help_text = "Weight in kilograms (min: 0.01kg)"
        self.fields['unit_price'].help_text = "Price per kilogram in UGX"
        self.fields['customer_contact'].help_text = "Phone or email for follow-up"
        self.fields['coffee_type'].initial = CoffeeSale.ARABICA



class InventoryForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = CoffeeInventory
        fields = ['coffee_category', 'coffee_type', 'quantity', 'unit', 'average_unit_cost']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'average_unit_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def setup_fields(self):
        self.fields['quantity'].help_text = "Current stock quantity"
        self.fields['average_unit_cost'].help_text = "Weighted average cost per unit"
        self.fields['unit'].initial = 'kg'

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        avg_cost = cleaned_data.get('average_unit_cost')
        
        if quantity is not None and quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        
        if avg_cost is not None and avg_cost < 0:
            raise ValidationError("Average unit cost cannot be negative")
        
        return cleaned_data