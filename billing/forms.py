from decimal import Decimal

from django import forms

from consumers.models import Consumer

from .models import Invoice, Payment


class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "consumer",
            "billing_period",
            "previous_reading",
            "current_reading",
            "due_date",
        ]
        widgets = {
            "consumer": forms.Select(attrs={"class": "form-select"}),
            "billing_period": forms.TextInput(attrs={"class": "form-control"}),
            "previous_reading": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "current_reading": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        previous = cleaned_data.get("previous_reading")
        current = cleaned_data.get("current_reading")
        if previous is not None and current is not None and current < previous:
            raise forms.ValidationError("Текущее показание не может быть меньше предыдущего.")
        return cleaned_data


class PaymentCreateForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "reference"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0.00"):
            raise forms.ValidationError("Сумма оплаты должна быть больше нуля.")
        return amount
