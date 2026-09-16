from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consumers.models import Consumer
from consumers.services import (
    create_consumer,
    create_contract,
    create_meter,
    create_meter_reading,
    create_supply_object,
)
from employee.forms import (
    ConsumerCreateForm,
    ContractForm,
    MeterForm,
    MeterReadingForm,
    SupplyObjectForm,
)


def is_employee(user) -> bool:
    return user.is_authenticated and user.is_employee


@login_required
@user_passes_test(is_employee)
def consumer_create_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ConsumerCreateForm(request.POST)
        if form.is_valid():
            create_consumer(
                account_number=form.cleaned_data["account_number"],
                full_name=form.cleaned_data["full_name"],
                address=form.cleaned_data["address"],
                contract_number=form.cleaned_data["contract_number"],
                tariff_rate=form.cleaned_data["tariff_rate"],
            )
            return redirect("consumer_list")
    else:
        form = ConsumerCreateForm()

    return render(
        request,
        "employee/consumer_create.html",
        {"form": form, "title": "Новый потребитель"},
    )


@login_required
@user_passes_test(is_employee)
def meter_reading_create_view(request: HttpRequest, consumer_id: int) -> HttpResponse:
    consumer = Consumer.objects.get(pk=consumer_id)

    if request.method == "POST":
        form = MeterReadingForm(request.POST)
        if form.is_valid():
            create_meter_reading(
                consumer=consumer,
                reading_date=form.cleaned_data["reading_date"],
                value=form.cleaned_data["value"],
            )
            return redirect("consumer_detail", pk=consumer.pk)
    else:
        form = MeterReadingForm()

    return render(
        request,
        "employee/meter_reading_create.html",
        {"form": form, "consumer": consumer, "title": "Добавить показание"},
    )


@login_required
@user_passes_test(is_employee)
def supply_object_create_view(request: HttpRequest) -> HttpResponse:
    form = SupplyObjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_supply_object(**form.cleaned_data)
        return redirect("employee_dashboard")
    return render(
        request, "employee/entity_create.html", {"form": form, "title": "Новый объект потребления"}
    )


@login_required
@user_passes_test(is_employee)
def contract_create_view(request: HttpRequest) -> HttpResponse:
    form = ContractForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_contract(**form.cleaned_data)
        return redirect("employee_dashboard")
    return render(request, "employee/entity_create.html", {"form": form, "title": "Новый договор"})


@login_required
@user_passes_test(is_employee)
def meter_create_view(request: HttpRequest) -> HttpResponse:
    form = MeterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_meter(**form.cleaned_data)
        return redirect("employee_dashboard")
    return render(
        request, "employee/entity_create.html", {"form": form, "title": "Новый прибор учета"}
    )
