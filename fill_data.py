from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from billing.services import create_invoice_for_consumer, register_payment  # noqa: E402
from consumers.models import Consumer, MeterReading  # noqa: E402
from notifications.services import create_notification  # noqa: E402


def populate_demo_data() -> None:
    Consumer.objects.all().delete()

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
        created_consumers.append(Consumer.objects.create(**data))

    for index, consumer in enumerate(created_consumers, start=1):
        MeterReading.objects.create(
            consumer=consumer,
            reading_date=date(2026, 8, 25),
            value=Decimal(f"{150 + index * 20}.000"),
        )
        MeterReading.objects.create(
            consumer=consumer,
            reading_date=date(2026, 9, 25),
            value=Decimal(f"{200 + index * 25}.500"),
        )

    invoice_1 = create_invoice_for_consumer(
        consumer=created_consumers[0],
        billing_period="2026-09",
        previous_reading=Decimal("150.000"),
        current_reading=Decimal("210.000"),
        due_date=date(2026, 9, 25),
    )
    invoice_2 = create_invoice_for_consumer(
        consumer=created_consumers[1],
        billing_period="2026-09",
        previous_reading=Decimal("160.000"),
        current_reading=Decimal("228.500"),
        due_date=date(2026, 9, 25),
    )
    create_invoice_for_consumer(
        consumer=created_consumers[2],
        billing_period="2026-09",
        previous_reading=Decimal("180.000"),
        current_reading=Decimal("230.500"),
        due_date=date(2026, 9, 25),
    )

    register_payment(invoice_1, invoice_1.total_amount, "TRANSFER", "REF-0001")
    register_payment(invoice_2, invoice_2.total_amount * Decimal("0.5"), "CARD", "REF-0002")

    create_notification(
        None,
        "Платёж обработан",
        "Оплата по счёту номер 1 успешно зачислена.",
        "SUCCESS",
    )
    create_notification(
        None,
        "Проверка показаний",
        "Необходимо уточнить данные по третьему абоненту.",
        "WARNING",
    )

    print("Demo data populated successfully.")


if __name__ == "__main__":
    populate_demo_data()
