from decimal import Decimal

import pytest
from django.urls import reverse

from consumers.models import Consumer

from .models import Invoice, Payment
from .services import create_invoice_for_consumer, register_payment


@pytest.mark.django_db
class TestBilling:
    def test_invoice_creation_calculates_consumption_and_total(self):
        consumer = Consumer.objects.create(
            account_number="A-2001",
            full_name="Иван Петров",
            address="ул. Полевая, 3",
            contract_number="K-2001",
            tariff_rate=Decimal("6.75"),
        )

        invoice = create_invoice_for_consumer(
            consumer=consumer,
            billing_period="2026-09",
            previous_reading=Decimal("180.000"),
            current_reading=Decimal("230.500"),
            due_date="2026-09-25",
        )

        assert invoice.consumption_kwh == Decimal("50.500")
        assert invoice.total_amount == Decimal("340.88")
        assert invoice.status == Invoice.Status.ISSUED

    def test_payment_marks_invoice_paid(self):
        consumer = Consumer.objects.create(
            account_number="A-2002",
            full_name="Мария Смирнова",
            address="ул. Солнечная, 11",
            contract_number="K-2002",
            tariff_rate=Decimal("5.90"),
        )

        invoice = create_invoice_for_consumer(
            consumer=consumer,
            billing_period="2026-09",
            previous_reading=Decimal("150.000"),
            current_reading=Decimal("190.000"),
            due_date="2026-09-25",
        )

        register_payment(invoice, invoice.total_amount, Payment.Method.TRANSFER, "REF-1001")

        invoice.refresh_from_db()
        assert invoice.status == Invoice.Status.PAID

    def test_invoice_create_view_renders_form_and_creates_invoice(self, client):
        consumer = Consumer.objects.create(
            account_number="A-2003",
            full_name="Ольга Ларина",
            address="ул. Горная, 40",
            contract_number="K-2003",
            tariff_rate=Decimal("5.40"),
        )

        response = client.post(
            reverse("invoice_create"),
            {
                "consumer": consumer.pk,
                "billing_period": "2026-10",
                "previous_reading": "120.000",
                "current_reading": "178.500",
                "due_date": "2026-10-25",
            },
        )

        assert response.status_code == 302
        invoice = Invoice.objects.get(consumer=consumer, billing_period="2026-10")
        assert invoice.total_amount == Decimal("315.90")

    def test_payment_create_view_marks_invoice_paid(self, client):
        consumer = Consumer.objects.create(
            account_number="A-2004",
            full_name="Павел Киселёв",
            address="ул. Дорожная, 9",
            contract_number="K-2004",
            tariff_rate=Decimal("4.50"),
        )

        invoice = create_invoice_for_consumer(
            consumer=consumer,
            billing_period="2026-10",
            previous_reading=Decimal("100.000"),
            current_reading=Decimal("140.000"),
            due_date="2026-10-25",
        )

        response = client.post(
            reverse("payment_create", kwargs={"invoice_id": invoice.pk}),
            {
                "amount": str(invoice.total_amount),
                "payment_method": Payment.Method.CARD,
                "reference": "REF-3001",
            },
        )

        invoice.refresh_from_db()
        assert response.status_code == 302
        assert invoice.status == Invoice.Status.PAID
