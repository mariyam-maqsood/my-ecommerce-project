from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    """Form for capturing shipping and contact details during checkout."""

    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'email': forms.EmailInput(
                attrs={'class': 'form-control'}
            ),
            'phone': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }