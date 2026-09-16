from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from billing.models import Invoice, Payment
from consumers.models import Consumer
from notifications.models import Notification


@login_required
def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_consumer:
        return redirect("consumer_dashboard")
    if request.user.is_employee:
        return redirect("employee_dashboard")

    consumers_count = Consumer.objects.count()
    invoices_count = Invoice.objects.count()
    paid_count = Invoice.objects.filter(status=Invoice.Status.PAID).count()
    total_revenue = Payment.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    latest_notifications = Notification.objects.select_related("user")[:5]

    context = {
        "title": "EnergoCheck",
        "consumers_count": consumers_count,
        "invoices_count": invoices_count,
        "paid_count": paid_count,
        "total_revenue": total_revenue,
        "latest_notifications": latest_notifications,
    }
    return render(request, "home.html", context)


@login_required
@user_passes_test(lambda user: user.is_employee)
def employee_dashboard(request: HttpRequest) -> HttpResponse:
    consumers = Consumer.objects.filter(is_active=True).order_by("full_name")
    unpaid_invoices = Invoice.objects.filter(
        status__in=[Invoice.Status.ISSUED, Invoice.Status.OVERDUE, Invoice.Status.DRAFT]
    ).select_related("consumer")[:10]

    return render(
        request,
        "employee_dashboard.html",
        {
            "title": "Панель сотрудника",
            "consumers": consumers,
            "unpaid_invoices": unpaid_invoices,
        },
    )


@login_required
@user_passes_test(lambda user: user.is_consumer)
def consumer_dashboard(request: HttpRequest) -> HttpResponse:
    consumer = request.user.consumer_profile
    invoices = consumer.invoices.select_related("contract").order_by("-issued_at")[:5]
    readings = consumer.meter_readings.select_related("meter").order_by("-reading_date")[:5]
    notifications = request.user.notifications.order_by("-created_at")[:5]
    return render(
        request,
        "consumer_dashboard.html",
        {
            "title": "Кабинет потребителя",
            "consumer": consumer,
            "invoices": invoices,
            "readings": readings,
            "notifications": notifications,
        },
    )
