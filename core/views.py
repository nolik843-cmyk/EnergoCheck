from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from billing.models import Invoice, Payment
from consumers.models import Consumer
from notifications.models import Notification


def home(request: HttpRequest) -> HttpResponse:
    consumers_count = Consumer.objects.count()
    invoices_count = Invoice.objects.count()
    paid_count = Invoice.objects.filter(status=Invoice.Status.PAID).count()
    total_revenue = (
        Payment.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    )
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
