from decimal import Decimal

from django import forms

from consumers.models import Consumer, Contract, Meter, SupplyObject


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


class SupplyObjectForm(forms.ModelForm):
    class Meta:
        model = SupplyObject
        fields = ["consumer", "address", "object_type", "area_m2", "residents_count", "status"]
        widgets = {
            "consumer": forms.Select(attrs={"class": "form-select"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "object_type": forms.TextInput(attrs={"class": "form-control"}),
            "area_m2": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "residents_count": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["consumer", "supply_object", "number", "start_date", "end_date", "status"]
        widgets = {
            "consumer": forms.Select(attrs={"class": "form-select"}),
            "supply_object": forms.Select(attrs={"class": "form-select"}),
            "number": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        consumer = cleaned_data.get("consumer")
        supply_object = cleaned_data.get("supply_object")
        if consumer and supply_object and supply_object.consumer_id != consumer.id:
            raise forms.ValidationError(
                "Объект потребления должен принадлежать выбранному потребителю."
            )
        return cleaned_data


class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = [
            "supply_object",
            "serial_number",
            "model_name",
            "meter_type",
            "install_date",
            "commissioning_reading",
            "multiplier",
            "phase_count",
            "status",
        ]
        widgets = {
            "supply_object": forms.Select(attrs={"class": "form-select"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "model_name": forms.TextInput(attrs={"class": "form-control"}),
            "meter_type": forms.TextInput(attrs={"class": "form-control"}),
            "install_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "commissioning_reading": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.001"}
            ),
            "multiplier": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "phase_count": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
