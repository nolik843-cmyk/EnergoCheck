from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from consumers.models import Consumer, Contract, Meter, MeterReading, SupplyObject

from .models import Invoice, Payment, Tariff
from .services import create_invoice_for_consumer, generate_invoice, register_payment

User = get_user_model()


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
        employee = User.objects.create_user(
            username="employee_invoice",
            password="StrongPass123!",
            role=User.Role.EMPLOYEE,
        )
        client.force_login(employee)
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
        employee = User.objects.create_user(
            username="employee_payment",
            password="StrongPass123!",
            role=User.Role.EMPLOYEE,
        )
        client.force_login(employee)
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

    def test_generate_invoice_uses_tariff_snapshot_and_is_idempotent(self):
        consumer = Consumer.objects.create(
            account_number="A-2010",
            full_name="Александр Волков",
            address="ул. Полевая, 10",
            contract_number="K-2010",
            tariff_rate=Decimal("4.00"),
        )
        supply_object = SupplyObject.objects.create(consumer=consumer, address=consumer.address)
        contract = Contract.objects.create(
            consumer=consumer,
            supply_object=supply_object,
            number="DOG-2010",
            start_date=date(2026, 1, 1),
        )
        meter = Meter.objects.create(
            supply_object=supply_object,
            serial_number="M-2010",
            install_date=date(2026, 1, 1),
        )
        MeterReading.objects.create(
            consumer=consumer,
            meter=meter,
            reading_date=date(2026, 9, 1),
            value=Decimal("100.000"),
        )
        MeterReading.objects.create(
            consumer=consumer,
            meter=meter,
            reading_date=date(2026, 9, 30),
            value=Decimal("150.000"),
        )
        tariff = Tariff.objects.create(
            name="Базовый 2026",
            price_per_kwh=Decimal("7.25"),
            valid_from=date(2026, 1, 1),
        )

        invoice = generate_invoice(
            contract=contract,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 30),
            due_date=date(2026, 10, 15),
            tariff=tariff,
        )
        duplicate = generate_invoice(
            contract=contract,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 30),
            due_date=date(2026, 10, 15),
            tariff=tariff,
        )

        assert invoice.pk == duplicate.pk
        assert invoice.tariff_name_snapshot == "Базовый 2026"
        assert invoice.total_amount == Decimal("362.50")

    def test_partial_payment_changes_invoice_status(self):
        consumer = Consumer.objects.create(
            account_number="A-2011",
            full_name="Вера Лукина",
            address="ул. Полевая, 11",
            contract_number="K-2011",
            tariff_rate=Decimal("5.00"),
        )
        invoice = create_invoice_for_consumer(
            consumer=consumer,
            billing_period="2026-11",
            previous_reading=Decimal("10.000"),
            current_reading=Decimal("20.000"),
            due_date="2026-11-25",
        )

        register_payment(invoice, Decimal("10.00"), Payment.Method.TRANSFER, "REF-2011")

        invoice.refresh_from_db()
        assert invoice.status == Invoice.Status.PARTIALLY_PAID
