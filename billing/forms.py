from decimal import Decimal

from django import forms

from .models import Invoice, Payment, Tariff


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
        fields = ["amount"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0.00"):
            raise forms.ValidationError("Сумма оплаты должна быть больше нуля.")
        return amount


class TariffForm(forms.ModelForm):
    class Meta:
        model = Tariff
        fields = ["name", "price_per_kwh", "valid_from", "valid_to", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price_per_kwh": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "valid_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "valid_to": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")
        if valid_from and valid_to and valid_to < valid_from:
            raise forms.ValidationError("Дата окончания тарифа не может быть раньше даты начала.")
        return cleaned_data
