from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from secrets import token_urlsafe

import django
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

from billing.models import Invoice, Tariff  # noqa: E402
from billing.services import register_payment  # noqa: E402
from consumers.models import Consumer, Contract, Meter, MeterReading, SupplyObject  # noqa: E402
from notifications.models import Notification  # noqa: E402

User = get_user_model()


@transaction.atomic
def populate_demo_data() -> None:
    employee_password = os.getenv("DEMO_EMPLOYEE_PASSWORD")
    consumer_password = os.getenv("DEMO_CONSUMER_PASSWORD")
    employee = get_or_create_demo_user(
        username="employee_demo",
        role=User.Role.EMPLOYEE,
        password=employee_password,
    )

    consumers = [
        {
            "account_number": "A-1001",
            "full_name": "Иван Иванов",
            "address": "ул. Лесная, 10",
            "contract_number": "K-1001",
            "tariff_rate": Decimal("5.50"),
        },
        {
            "account_number": "A-1002",
            "full_name": "Мария Петрова",
            "address": "ул. Садовая, 22",
            "contract_number": "K-1002",
            "tariff_rate": Decimal("6.20"),
        },
        {
            "account_number": "A-1003",
            "full_name": "Алексей Смирнов",
            "address": "ул. Озерная, 7",
            "contract_number": "K-1003",
            "tariff_rate": Decimal("7.10"),
        },
    ]

    created_consumers = []
    for data in consumers:
        consumer, _ = Consumer.objects.update_or_create(
            account_number=data["account_number"],
            defaults=data,
        )
        username = (
            "consumer_demo"
            if data["account_number"] == "A-1001"
            and User.objects.filter(username="consumer_demo").exists()
            else f"consumer_{data['account_number'].lower().replace('-', '_')}"
        )
        consumer_user = get_or_create_demo_user(
            username=username,
            role=User.Role.CONSUMER,
            password=consumer_password,
        )
        if consumer.user_id != consumer_user.id:
            consumer.user = consumer_user
            consumer.save(update_fields=["user"])
        created_consumers.append(consumer)

    _tariff, _ = Tariff.objects.get_or_create(
        name="Демо-тариф 2026",
        valid_from=date(2026, 1, 1),
        defaults={"price_per_kwh": Decimal("6.20"), "is_active": True},
    )

    meters = []
    for index, consumer in enumerate(created_consumers, start=1):
        supply_object, _ = SupplyObject.objects.get_or_create(
            consumer=consumer,
            address=consumer.address,
            defaults={
                "object_type": "Квартира",
                "area_m2": Decimal("54.20"),
                "residents_count": 2,
            },
        )
        Contract.objects.get_or_create(
            number=consumer.contract_number,
            defaults={
                "consumer": consumer,
                "supply_object": supply_object,
                "start_date": date(2026, 1, 1),
                "status": Contract.Status.ACTIVE,
            },
        )
        meter, _ = Meter.objects.get_or_create(
            serial_number=f"M-{index:04d}",
            defaults={
                "supply_object": supply_object,
                "model_name": "Демо-Счетчик",
                "install_date": date(2026, 1, 1),
            },
        )
        meters.append(meter)

    for index, (consumer, meter) in enumerate(zip(created_consumers, meters, strict=True), start=1):
        MeterReading.objects.get_or_create(
            consumer=consumer,
            meter=meter,
            reading_date=date(2026, 8, 25),
            defaults={"value": Decimal(f"{150 + index * 20}.000")},
        )
        MeterReading.objects.get_or_create(
            consumer=consumer,
            meter=meter,
            reading_date=date(2026, 9, 25),
            defaults={"value": Decimal(f"{200 + index * 25}.500")},
        )

    invoice_1 = get_or_create_demo_invoice(
        consumer=created_consumers[0],
        billing_period="2026-09",
        previous_reading=Decimal("150.000"),
        current_reading=Decimal("210.000"),
        due_date=date(2026, 9, 25),
    )
    invoice_2 = get_or_create_demo_invoice(
        consumer=created_consumers[1],
        billing_period="2026-09",
        previous_reading=Decimal("160.000"),
        current_reading=Decimal("228.500"),
        due_date=date(2026, 9, 25),
    )
    get_or_create_demo_invoice(
        consumer=created_consumers[2],
        billing_period="2026-09",
        previous_reading=Decimal("180.000"),
        current_reading=Decimal("230.500"),
        due_date=date(2026, 9, 25),
    )

    if not invoice_1.payments.filter(reference="REF-0001").exists():
        register_payment(invoice_1, invoice_1.total_amount, "TRANSFER", "REF-0001")
    if not invoice_2.payments.filter(reference="REF-0002").exists():
        register_payment(invoice_2, invoice_2.total_amount * Decimal("0.5"), "CARD", "REF-0002")

    Notification.objects.get_or_create(
        user=employee,
        title="Платёж обработан",
        defaults={
            "message": "Оплата по счёту номер 1 успешно зачислена.",
            "notification_type": "SUCCESS",
        },
    )
    Notification.objects.get_or_create(
        user=employee,
        title="Проверка показаний",
        defaults={
            "message": "Необходимо уточнить данные по третьему абоненту.",
            "notification_type": "WARNING",
        },
    )

    print("Demo data populated successfully.")
    print("Employee login: employee_demo")
    print("Consumer login: consumer_demo")
    if employee_password is None or consumer_password is None:
        print("Set DEMO_EMPLOYEE_PASSWORD and DEMO_CONSUMER_PASSWORD to use stable passwords.")


def get_or_create_demo_user(*, username: str, role: str, password: str | None) -> User:
    user, created = User.objects.get_or_create(username=username, defaults={"role": role})
    if created:
        generated_password = password or token_urlsafe(16)
        user.set_password(generated_password)
        user.role = role
        user.save(update_fields=["password", "role"])
        print(f"Generated password for {username}: {generated_password}")
    elif user.role != role:
        user.role = role
        user.save(update_fields=["role"])
    return user


def get_or_create_demo_invoice(**kwargs):
    invoice, _ = Invoice.objects.get_or_create(
        consumer=kwargs["consumer"],
        billing_period=kwargs["billing_period"],
        defaults={
            "previous_reading": kwargs["previous_reading"],
            "current_reading": kwargs["current_reading"],
            "due_date": kwargs["due_date"],
            "tariff_rate": kwargs.get("tariff_rate") or kwargs["consumer"].tariff_rate,
            "consumption_kwh": kwargs["current_reading"] - kwargs["previous_reading"],
            "total_amount": (
                (kwargs["current_reading"] - kwargs["previous_reading"])
                * (kwargs.get("tariff_rate") or kwargs["consumer"].tariff_rate)
            ).quantize(Decimal("0.01")),
            "status": Invoice.Status.ISSUED,
        },
    )
    return invoice


if __name__ == "__main__":
    populate_demo_data()
