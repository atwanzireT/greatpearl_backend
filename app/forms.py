from django import forms
from .models import Customer, CoffeeMilling, Payment

class CustomerForm(forms.ModelForm):
    """
    Form for registering a new customer.
    """
    class Meta:
        model = Customer
        fields = ["name", "phone"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
        }

class CoffeeMillingForm(forms.ModelForm):
    """
    Form for recording coffee milling transactions.
    """
    class Meta:
        model = CoffeeMilling
        fields = [
            "customer", 
            "hulled_coffee_weight", 
            "cost_per_kg",
            "milling_status",
            "notes"
        ]
        widgets = {
            "customer": forms.Select(attrs={"class": "form-control"}),
            "hulled_coffee_weight": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Hulled Coffee Weight (Kg)"}),
            "cost_per_kg": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Milling Cost per Kg"}),
            "milling_status": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "placeholder": "Additional Notes", "rows": 3}),
        }

class PaymentForm(forms.ModelForm):
    """
    Form for processing payments for milling.
    """
    class Meta:
        model = Payment
        fields = ["customer", "milling_record", "amount_paid",]
        widgets = {
            "customer": forms.Select(attrs={"class": "form-control"}),
            "milling_record": forms.Select(attrs={"class": "form-control"}),
            "amount_paid": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount Paid"})
        }