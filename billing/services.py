from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from consumers.models import Consumer, Contract

from .models import Invoice, Payment, Tariff


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


def get_tariff_for_date(target_date: date) -> Tariff:
    return Tariff.objects.get(
        valid_from__lte=target_date,
        is_active=True,
    )


@transaction.atomic
def generate_invoice(
    *,
    contract: Contract,
    period_start: date,
    period_end: date,
    due_date: date,
    tariff: Tariff | None = None,
) -> Invoice:
    existing = Invoice.objects.filter(
        contract=contract,
        billing_period=period_end.strftime("%Y-%m"),
    ).first()
    if existing is not None:
        return existing

    readings = contract.consumer.meter_readings.filter(
        status="CONFIRMED",
        reading_date__gte=period_start,
        reading_date__lte=period_end,
    ).order_by("reading_date")
    first_reading = readings.first()
    last_reading = readings.last()
    if first_reading is None or last_reading is None or first_reading == last_reading:
        raise ValueError("Недостаточно подтвержденных показаний за расчетный период.")

    selected_tariff = tariff or get_tariff_for_date(period_end)
    consumption = last_reading.value - first_reading.value
    return Invoice.objects.create(
        consumer=contract.consumer,
        contract=contract,
        billing_period=period_end.strftime("%Y-%m"),
        previous_reading=first_reading.value,
        current_reading=last_reading.value,
        consumption_kwh=consumption,
        tariff_rate=selected_tariff.price_per_kwh,
        tariff_name_snapshot=selected_tariff.name,
        price_per_kwh_snapshot=selected_tariff.price_per_kwh,
        total_amount=(consumption * selected_tariff.price_per_kwh).quantize(Decimal("0.01")),
        due_date=due_date,
        status=Invoice.Status.ISSUED,
    )


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
    elif total_paid > Decimal("0.00"):
        invoice.status = Invoice.Status.PARTIALLY_PAID
        invoice.save(update_fields=["status"])

    return payment
