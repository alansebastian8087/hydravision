from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['sample', 'amount', 'payment_method', 'payment_status', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ClientPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.Select(),
        }


class AdminPaymentApprovalForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }