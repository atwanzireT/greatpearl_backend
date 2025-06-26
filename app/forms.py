from django import forms
from django_select2 import forms as s2forms
from .models import Customer, MillingProcess, CustomerAccount, MillingTransaction, Supplier, CoffeePurchase, CoffeeSale
from django.contrib.auth import get_user_model

User = get_user_model()

# Custom Select2 widgets with enhanced styling
class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "phone__icontains",
        "id__icontains",
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ease-in-out bg-white shadow-sm hover:shadow-md',
            'data-placeholder': 'Search or select customer...',
            'data-allow-clear': 'true'
        })

class SupplierWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "phone__icontains",
        "id__icontains",
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ease-in-out bg-white shadow-sm hover:shadow-md',
            'data-placeholder': 'Search or select supplier...',
            'data-allow-clear': 'true'
        })

class CustomerAccountWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "customer__name__icontains",
        "customer__phone__icontains",
        "customer__id__icontains",
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ease-in-out bg-white shadow-sm hover:shadow-md',
            'data-placeholder': 'Search or select customer account...',
            'data-allow-clear': 'true'
        })

class MillingProcessWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "customer__name__icontains",
        "id__icontains",
        
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ease-in-out bg-white shadow-sm hover:shadow-md',
            'data-placeholder': 'Search or select milling process...',
            'data-allow-clear': 'true'
        })

class UserWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "username__icontains",
        "email__icontains",
        "first_name__icontains",
        "last_name__icontains",
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ease-in-out bg-white shadow-sm hover:shadow-md',
            'data-placeholder': 'Search or select user...',
            'data-allow-clear': 'true'
        })

class EnhancedTailwindFormMixin:
    """Enhanced form mixin with modern Tailwind CSS styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_styling()
    
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
                error_classes = ' border-red-500 focus:ring-red-500 focus:border-red-500 bg-red-50'
                base_classes += error_classes
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
                    'class': (
                        'text-blue-600 bg-white border-gray-300 '
                        'focus:ring-blue-500 focus:ring-2'
                    )
                })
            
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': f'{base_classes} pr-10 cursor-pointer appearance-none bg-select-arrow bg-no-repeat bg-right bg-center'
                })
            
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': f'{base_classes} resize-none min-h-[100px]',
                    'rows': field.widget.attrs.get('rows', 4)
                })
            
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({
                    'class': f'{base_classes} datepicker cursor-pointer',
                    'type': 'date',
                    'autocomplete': 'off'
                })
            
            elif isinstance(field.widget, forms.DateTimeInput):
                field.widget.attrs.update({
                    'class': f'{base_classes} datetimepicker cursor-pointer',
                    'type': 'datetime-local',
                    'autocomplete': 'off'
                })
            
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.update({
                    'class': f'{base_classes} text-right font-mono',
                    'autocomplete': 'off'
                })
            
            elif isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({
                    'class': f'{base_classes}',
                    'autocomplete': 'email'
                })
            
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({
                    'class': f'{base_classes}',
                    'autocomplete': 'current-password'
                })
            
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    'class': (
                        'w-full px-4 py-3 border border-gray-300 rounded-lg '
                        'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                        'file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
                        'file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 '
                        'hover:file:bg-blue-100 file:cursor-pointer cursor-pointer'
                    )
                })
            
            else:
                # Default text input styling
                field.widget.attrs.update({
                    'class': f'{base_classes}',
                    'autocomplete': 'off'
                })

# Enhanced form classes
class CustomerForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter customer full name',
                'maxlength': '255'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter phone number (e.g., +256701234567)',
                'maxlength': '20'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Customer's full legal name"
        self.fields['phone'].help_text = "Unique phone number for this customer"

class MillingProcessForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = MillingProcess
        fields = ['customer', 'hulled_weight', 'notes']
        widgets = {
            'customer': CustomerWidget,
            'hulled_weight': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.1'
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': 'Additional notes about this milling process...',
                'rows': 3
            }),
        }
    

class CustomerAccountForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = CustomerAccount
        fields = ['customer', 'balance']
        widgets = {
            'customer': CustomerWidget,
            'balance': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['balance'].help_text = "Initial account balance in UGX"


class TransactionForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = MillingTransaction
        fields = ['account', 'amount', 'transaction_type', 'reference', 'milling_process']
        widgets = {
            'account': CustomerAccountWidget,
            'amount': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'reference': forms.TextInput(attrs={
                'placeholder': 'Enter transaction reference',
                'maxlength': '50'
            }),
            'milling_process': MillingProcessWidget,
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.instance.created_by = user
        
        # Set default to Credit
        self.fields['transaction_type'].initial = MillingTransaction.CREDIT


class SupplierForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter supplier company name',
                'maxlength': '255'
            }),
            'contact_person': forms.TextInput(attrs={
                'placeholder': 'Enter contact person name',
                'maxlength': '255'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter phone number',
                'maxlength': '20'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'supplier@example.com'
            }),
            'address': forms.Textarea(attrs={
                'placeholder': 'Enter full address including district and region...',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.created_by = user
        
        self.fields['name'].help_text = "Official supplier/company name"
        self.fields['contact_person'].help_text = "Primary contact person"
        self.fields['email'].help_text = "Business email address"

class CoffeePurchaseForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = CoffeePurchase
        fields = ['supplier', 'coffee_category', 'coffee_type', 'quantity', 'unit_price', 
                 'purchase_date', 'delivery_date', 'notes']
        widgets = {
            'supplier': SupplierWidget,
            'quantity': forms.NumberInput(attrs={
                'placeholder': '0',
                'step': '1',
                'min': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'placeholder': '0',
                'step': '1',
                'min': '1'
            }),
            'purchase_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'delivery_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': 'Additional notes about this purchase...',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.recorded_by = user
        
        self.fields['quantity'].help_text = "Weight in kilograms"
        self.fields['unit_price'].help_text = "Price per kilogram in UGX"
        self.fields['delivery_date'].help_text = "Expected or actual delivery date"


class CoffeeSaleForm(EnhancedTailwindFormMixin, forms.ModelForm):
    class Meta:
        model = CoffeeSale
        fields = [
            'customer', 
            'customer_address',
            'customer_contact',
            'coffee_category',
            'coffee_type',
            'quantity', 
            'unit_price', 
            'sale_date', 
            'notes'
        ]
        widgets = {
            'customer': forms.TextInput(attrs={
                'placeholder': 'Enter customer full name',
                'maxlength': '255',
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'customer_address': forms.TextInput(attrs={
                'placeholder': 'Customer physical address',
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'customer_contact': forms.TextInput(attrs={
                'placeholder': 'Phone number or email',
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'unit_price': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'sale_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': 'Additional notes about this sale...',
                'rows': 3,
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'coffee_category': forms.Select(attrs={
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
            'coffee_type': forms.Select(attrs={
                'class': 'focus:ring-coffee-500 focus:border-coffee-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.instance.recorded_by = user
        
        # Improved help texts
        self.fields['quantity'].help_text = "Weight in kilograms (min: 0.01kg)"
        self.fields['unit_price'].help_text = "Price per kilogram in UGX (min: 0.01 UGX)"
        self.fields['sale_date'].help_text = "Date of the sale transaction"
        self.fields['customer_contact'].help_text = "Phone number or email for follow-up"
        
        # Set default coffee type to Arabica
        self.fields['coffee_type'].initial = CoffeeSale.ARABICA
        
        # Add autofocus to customer field
        self.fields['customer'].widget.attrs['autofocus'] = True
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero")
        return quantity
    
    def clean_unit_price(self):
        unit_price = self.cleaned_data['unit_price']
        if unit_price <= 0:
            raise forms.ValidationError("Unit price must be greater than zero")
        return unit_price
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        
        # Calculate and display estimated total
        if quantity and unit_price:
            self.estimated_total = quantity * unit_price
        else:
            self.estimated_total = None
            
        return cleaned_data