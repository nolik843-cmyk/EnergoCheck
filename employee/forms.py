from decimal import Decimal

from django import forms

from consumers.models import Consumer


class ConsumerCreateForm(forms.ModelForm):
    class Meta:
        model = Consumer
        fields = [
            "account_number",
            "full_name",
            "address",
            "contract_number",
            "tariff_rate",
            "is_active",
        ]
        widgets = {
            "account_number": forms.TextInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "contract_number": forms.TextInput(attrs={"class": "form-control"}),
            "tariff_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_tariff_rate(self):
        value = self.cleaned_data["tariff_rate"]
        if value < Decimal("0.00"):
            raise forms.ValidationError("Тариф не может быть отрицательным.")
        return value


class MeterReadingForm(forms.Form):
    reading_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    value = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=3,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
    )
