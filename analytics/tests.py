from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from billing.models import Invoice, Payment
from consumers.models import Consumer

User = get_user_model()


@pytest.mark.django_db
def test_analytics_requires_employee(client):
    consumer_user = User.objects.create_user(
        username="analytics_consumer", password="StrongPass123!", role=User.Role.CONSUMER
    )
    client.force_login(consumer_user)
    assert client.get(reverse("analytics_dashboard")).status_code == 302
    assert client.get(reverse("analytics_invoices_csv")).status_code == 302

    employee = User.objects.create_user(
        username="analytics_employee", password="StrongPass123!", role=User.Role.EMPLOYEE
    )
    client.force_login(employee)
    assert client.get(reverse("analytics_dashboard")).status_code == 200
    assert client.get(reverse("analytics_invoices_csv")).status_code == 200


@pytest.mark.django_db
def test_csv_exports_successful_payments_only(client):
    employee = User.objects.create_user(
        username="analytics_csv_employee",
        password="StrongPass123!",
        role=User.Role.EMPLOYEE,
    )
    consumer = Consumer.objects.create(
        account_number="A-CSV-1",
        full_name="Тестовый потребитель",
        address="Тестовая, 1",
        contract_number="C-CSV-1",
        tariff_rate=Decimal("5.00"),
    )
    invoice = Invoice.objects.create(
        consumer=consumer,
        billing_period="2026-11",
        previous_reading=Decimal("100.000"),
        current_reading=Decimal("120.000"),
        tariff_rate=Decimal("5.00"),
        total_amount=Decimal("100.00"),
        due_date=date(2026, 11, 25),
    )
    Payment.objects.create(
        invoice=invoice, amount=Decimal("30.00"),
        reference="CSV-PAID", status=Payment.Status.SUCCESS,
    )
    Payment.objects.create(
        invoice=invoice, amount=Decimal("10.00"),
        reference="CSV-FAILED", status=Payment.Status.FAILED,
    )
    client.force_login(employee)
    response = client.get(reverse("analytics_invoices_csv"))
    assert response.status_code == 200
    assert 'attachment;' in response["Content-Disposition"]
    text = response.content.decode("utf-8-sig")
    assert "A-CSV-1" in text
    assert "30.00" in text
    assert "70.00" in text
