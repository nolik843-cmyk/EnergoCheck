from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from integrations.meter_ocr import MeterReadingRecognizer

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


def submit_manual_reading(
    *,
    consumer: Consumer,
    reading_date: date,
    value: Decimal,
    meter: Meter | None = None,
    entered_by=None,
) -> MeterReading:
    if meter is not None and meter.supply_object.consumer_id != consumer.id:
        raise ValidationError("Выбранный прибор учета не принадлежит потребителю.")

    readings = MeterReading.objects.filter(consumer=consumer, reading_date=reading_date)
    if meter is not None:
        readings = readings.filter(meter=meter)
    if readings.filter(value=value).exists():
        raise ValidationError("Показание с такой датой и значением уже передано.")

    confirmed = MeterReading.objects.filter(
        consumer=consumer,
        status=MeterReading.Status.CONFIRMED,
    )
    if meter is not None:
        confirmed = confirmed.filter(meter=meter)
    previous = confirmed.order_by("-reading_date", "-created_at").first()
    status = MeterReading.Status.CONFIRMED
    confirmed_at = timezone.now()
    if previous is not None and value < previous.value:
        status = MeterReading.Status.PENDING_REVIEW
        confirmed_at = None

    return MeterReading.objects.create(
        consumer=consumer,
        meter=meter,
        reading_date=reading_date,
        value=value,
        source=(
            MeterReading.Source.EMPLOYEE
            if entered_by is not None and getattr(entered_by, "is_employee", False)
            else MeterReading.Source.MANUAL
        ),
        status=status,
        confirmed_at=confirmed_at,
    )


def get_readings_pending_review() -> QuerySet[MeterReading]:
    return MeterReading.objects.filter(status=MeterReading.Status.PENDING_REVIEW).select_related(
        "consumer", "meter"
    )


def review_meter_reading(
    *, reading: MeterReading, approved: bool, reviewer, comment: str = ""
) -> MeterReading:
    reading.status = MeterReading.Status.CONFIRMED if approved else MeterReading.Status.REJECTED
    reading.review_comment = comment
    reading.confirmed_at = timezone.now() if approved else None
    reading.save(update_fields=["status", "review_comment", "confirmed_at"])
    return reading


def recognize_photo_reading(
    *,
    consumer: Consumer,
    meter: Meter,
    reading_date: date,
    photo,
    recognizer: MeterReadingRecognizer,
    entered_by=None,
    confidence_threshold: Decimal = Decimal("0.75"),
) -> MeterReading:
    if meter.supply_object.consumer_id != consumer.id:
        raise ValidationError("Выбранный прибор учета не принадлежит потребителю.")

    try:
        image = Image.open(photo)
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("Файл не является корректным изображением.") from exc

    photo.seek(0)
    temporary_path = Path(getattr(photo, "temporary_file_path", lambda: "")())
    result = (
        recognizer.recognize(temporary_path)
        if temporary_path
        else recognizer.recognize(Path(photo.name))
    )
    value = result.value or Decimal("0.000")
    status = (
        MeterReading.Status.CONFIRMED
        if result.value is not None and result.confidence >= confidence_threshold
        else MeterReading.Status.PENDING_REVIEW
    )
    reading = MeterReading.objects.create(
        consumer=consumer,
        meter=meter,
        reading_date=reading_date,
        value=value,
        source=MeterReading.Source.PHOTO,
        status=status,
        photo=photo,
        recognized_value=result.value,
        recognition_confidence=result.confidence,
        review_comment=result.diagnostic,
        confirmed_at=timezone.now() if status == MeterReading.Status.CONFIRMED else None,
    )
    return reading


def create_supply_object(**kwargs) -> SupplyObject:
    return SupplyObject.objects.create(**kwargs)


def create_contract(**kwargs) -> Contract:
    return Contract.objects.create(**kwargs)


def create_meter(**kwargs) -> Meter:
    return Meter.objects.create(**kwargs)


def calculate_monthly_bill(consumer: Consumer, delta_kwh: Decimal) -> Decimal:
    return (delta_kwh * consumer.tariff_rate).quantize(Decimal("0.01"))
