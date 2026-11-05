from __future__ import annotations

import csv
from decimal import Decimal

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from billing.models import Invoice, Payment

from .services import get_dashboard_summary


def is_employee(user) -> bool:
    return user.is_authenticated and user.is_employee


@login_required
@user_passes_test(is_employee)
def analytics_dashboard(request: HttpRequest) -> HttpResponse:
    summary = get_dashboard_summary()
    return render(request, "analytics/dashboard.html", {"summary": summary, "title": "Аналитика"})


@login_required
@user_passes_test(is_employee)
def export_invoices_csv(request: HttpRequest) -> HttpResponse:
    """Export invoice/payment balances without granting consumer access to others' data."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="energo-invoices.csv"'
    response.write("\ufeff")  # UTF-8 BOM for Microsoft Excel.
    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "Лицевой счёт", "Потребитель", "Период", "Начислено, руб.",
        "Оплачено, руб.", "Остаток, руб.", "Статус",
    ])

    invoices = (
        Invoice.objects.select_related("consumer")
        .prefetch_related("payments")
        .order_by("consumer__account_number", "billing_period", "pk")
    )
    for invoice in invoices:
        paid = sum(
            (payment.amount for payment in invoice.payments.all()
             if payment.status == Payment.Status.SUCCESS),
            Decimal("0.00"),
        )
        balance = invoice.total_amount - paid
        writer.writerow([
            invoice.consumer.account_number,
            invoice.consumer.full_name,
            invoice.billing_period,
            invoice.total_amount,
            paid,
            balance,
            invoice.get_status_display(),
        ])
    return response
