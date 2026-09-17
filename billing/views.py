from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import InvoiceCreateForm, PaymentCreateForm, TariffForm
from .models import Invoice
from .services import create_invoice_for_consumer, register_demo_payment


def is_employee(user) -> bool:
    return user.is_authenticated and user.is_employee


def can_pay_invoice(user, invoice: Invoice) -> bool:
    return user.is_employee or invoice.consumer.user_id == user.id


@login_required
@user_passes_test(is_employee)
def billing_dashboard(request: HttpRequest) -> HttpResponse:
    invoices = Invoice.objects.select_related("consumer").all()
    return render(request, "billing/dashboard.html", {"invoices": invoices, "title": "Биллинг"})


@login_required
@user_passes_test(is_employee)
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


@login_required
def payment_create_view(request: HttpRequest, invoice_id: int) -> HttpResponse:
    invoice = Invoice.objects.get(pk=invoice_id)
    if not can_pay_invoice(request.user, invoice):
        return redirect("consumer_dashboard")

    if request.method == "POST":
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            try:
                register_demo_payment(
                    invoice_id=invoice.pk,
                    amount=form.cleaned_data["amount"],
                    user=request.user,
                )
            except ValidationError as error:
                form.add_error("amount", error.message)
            else:
                return redirect(
                    "consumer_dashboard" if request.user.is_consumer else "billing_dashboard"
                )
    else:
        form = PaymentCreateForm(initial={"amount": invoice.total_amount})

    return render(
        request,
        "billing/payment_create.html",
        {
            "form": form,
            "invoice": invoice,
            "title": "Оплата счёта",
            "demo_payment": True,
        },
    )


@login_required
@user_passes_test(is_employee)
def tariff_create_view(request: HttpRequest) -> HttpResponse:
    form = TariffForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("billing_dashboard")
    return render(request, "billing/tariff_create.html", {"form": form, "title": "Новый тариф"})
