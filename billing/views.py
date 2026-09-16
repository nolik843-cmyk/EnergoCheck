from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import InvoiceCreateForm, PaymentCreateForm
from .models import Invoice
from .services import create_invoice_for_consumer, register_payment


def billing_dashboard(request: HttpRequest) -> HttpResponse:
    invoices = Invoice.objects.select_related("consumer").all()
    return render(request, "billing/dashboard.html", {"invoices": invoices, "title": "Биллинг"})


def invoice_create_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = InvoiceCreateForm(request.POST)
        if form.is_valid():
            create_invoice_for_consumer(
                consumer=form.cleaned_data["consumer"],
                billing_period=form.cleaned_data["billing_period"],
                previous_reading=form.cleaned_data["previous_reading"],
                current_reading=form.cleaned_data["current_reading"],
                due_date=form.cleaned_data["due_date"],
                tariff_rate=form.cleaned_data["consumer"].tariff_rate,
            )
            return redirect("billing_dashboard")
    else:
        form = InvoiceCreateForm()

    return render(request, "billing/invoice_create.html", {"form": form, "title": "Создать счёт"})


def payment_create_view(request: HttpRequest, invoice_id: int) -> HttpResponse:
    invoice = Invoice.objects.get(pk=invoice_id)

    if request.method == "POST":
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            register_payment(
                invoice=invoice,
                amount=form.cleaned_data["amount"],
                method=form.cleaned_data["payment_method"],
                reference=form.cleaned_data["reference"],
            )
            return redirect("billing_dashboard")
    else:
        form = PaymentCreateForm(initial={"amount": invoice.total_amount})

    return render(
        request,
        "billing/payment_create.html",
        {"form": form, "invoice": invoice, "title": "Оплата счёта"},
    )
