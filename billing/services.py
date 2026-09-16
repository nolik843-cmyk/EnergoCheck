from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.utils import timezone

from consumers.models import Consumer

from .models import Invoice, Payment


def create_invoice_for_consumer(
    consumer: Consumer,
    billing_period: str,
    previous_reading: Decimal,
    current_reading: Decimal,
    due_date: date,
    tariff_rate: Decimal | None = None,
) -> Invoice:
    rate = tariff_rate or consumer.tariff_rate
    consumption = current_reading - previous_reading
    invoice = Invoice.objects.create(
        consumer=consumer,
        billing_period=billing_period,
        previous_reading=previous_reading,
        current_reading=current_reading,
        consumption_kwh=consumption,
        tariff_rate=rate,
        total_amount=(consumption * rate).quantize(Decimal("0.01")),
        due_date=due_date,
        status=Invoice.Status.ISSUED,
    )
    return invoice


def register_payment(invoice: Invoice, amount: Decimal, method: str, reference: str) -> Payment:
    payment = Payment.objects.create(
        invoice=invoice,
        amount=amount,
        payment_method=method,
        reference=reference,
    )

    total_paid = sum(
        (item.amount for item in invoice.payments.all()),
        Decimal("0.00"),
    )
    if total_paid >= invoice.total_amount:
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=["status", "paid_at"])
    elif invoice.status == Invoice.Status.PAID:
        invoice.status = Invoice.Status.ISSUED
        invoice.save(update_fields=["status"])

    return payment
