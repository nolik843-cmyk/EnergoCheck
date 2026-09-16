from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import QuerySet

from .models import Consumer, Contract, Meter, MeterReading, SupplyObject


def get_active_consumers() -> QuerySet[Consumer]:
    return Consumer.objects.filter(is_active=True).select_related("user")


def get_consumer_by_id(pk: int) -> Consumer:
    return Consumer.objects.get(pk=pk)


def create_consumer(
    *,
    account_number: str,
    full_name: str,
    address: str,
    contract_number: str,
    tariff_rate: Decimal,
    user=None,
) -> Consumer:
    return Consumer.objects.create(
        user=user,
        account_number=account_number,
        full_name=full_name,
        address=address,
        contract_number=contract_number,
        tariff_rate=tariff_rate,
        is_active=True,
    )


def create_meter_reading(
    consumer: Consumer,
    reading_date: date,
    value: Decimal,
) -> MeterReading:
    return MeterReading.objects.create(
        consumer=consumer,
        reading_date=reading_date,
        value=value,
    )


def create_supply_object(**kwargs) -> SupplyObject:
    return SupplyObject.objects.create(**kwargs)


def create_contract(**kwargs) -> Contract:
    return Contract.objects.create(**kwargs)


def create_meter(**kwargs) -> Meter:
    return Meter.objects.create(**kwargs)


def calculate_monthly_bill(consumer: Consumer, delta_kwh: Decimal) -> Decimal:
    return (delta_kwh * consumer.tariff_rate).quantize(Decimal("0.01"))
