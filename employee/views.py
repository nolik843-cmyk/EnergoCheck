from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from consumers.models import Consumer, Meter, MeterReading
from consumers.services import (
    create_consumer,
    create_contract,
    create_meter,
    create_supply_object,
    get_readings_pending_review,
    recognize_photo_reading,
    review_meter_reading,
    submit_manual_reading,
)
from employee.forms import (
    ConsumerCreateForm,
    ContractForm,
    MeterForm,
    MeterReadingForm,
    PhotoReadingForm,
    SupplyObjectForm,
)
from integrations.meter_ocr.fake import FakeMeterReadingRecognizer


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
    meters = Meter.objects.filter(
        supply_object__consumer=consumer,
        status=Meter.Status.ACTIVE,
    )

    if request.method == "POST":
        form = MeterReadingForm(request.POST, meters=meters)
        if form.is_valid():
            submit_manual_reading(
                consumer=consumer,
                reading_date=form.cleaned_data["reading_date"],
                value=form.cleaned_data["value"],
                meter=form.cleaned_data["meter"],
                entered_by=request.user,
            )
            return redirect("consumer_detail", pk=consumer.pk)
    else:
        form = MeterReadingForm(meters=meters)

    return render(
        request,
        "employee/meter_reading_create.html",
        {"form": form, "consumer": consumer, "title": "Добавить показание"},
    )


@login_required
@user_passes_test(is_employee)
def meter_reading_review_view(request: HttpRequest) -> HttpResponse:
    readings = get_readings_pending_review()
    return render(
        request,
        "employee/meter_reading_review.html",
        {"readings": readings, "title": "Проверка показаний"},
    )


@login_required
@user_passes_test(is_employee)
def meter_reading_review_action_view(request: HttpRequest, reading_id: int) -> HttpResponse:
    reading = get_object_or_404(MeterReading, pk=reading_id)
    if request.method == "POST":
        approved = request.POST.get("action") == "approve"
        review_meter_reading(
            reading=reading,
            approved=approved,
            reviewer=request.user,
            comment=request.POST.get("comment", ""),
        )
    return redirect("meter_reading_review")


@login_required
@user_passes_test(is_employee)
def photo_reading_create_view(request: HttpRequest, consumer_id: int) -> HttpResponse:
    consumer = get_object_or_404(Consumer, pk=consumer_id)
    meters = Meter.objects.filter(supply_object__consumer=consumer, status=Meter.Status.ACTIVE)
    form = PhotoReadingForm(request.POST or None, request.FILES or None, meters=meters)
    result = None
    if request.method == "POST" and form.is_valid():
        result = recognize_photo_reading(
            consumer=consumer,
            meter=form.cleaned_data["meter"],
            reading_date=form.cleaned_data["reading_date"],
            photo=form.cleaned_data["photo"],
            recognizer=FakeMeterReadingRecognizer(None),
            entered_by=request.user,
        )
    return render(
        request,
        "employee/photo_reading_create.html",
        {"form": form, "consumer": consumer, "result": result, "title": "Распознавание показания"},
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
