from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Consumer(models.Model):
    class Meta:
        verbose_name = "Потребитель"
        verbose_name_plural = "Потребители"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consumer_profile",
        blank=True,
        null=True,
    )
    account_number = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    contract_number = models.CharField(max_length=50, unique=True)
    tariff_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.account_number})"


class SupplyObject(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Активен"
        SUSPENDED = "SUSPENDED", "Приостановлен"
        CLOSED = "CLOSED", "Закрыт"

    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.CASCADE,
        related_name="supply_objects",
    )
    address = models.CharField(max_length=255)
    object_type = models.CharField(max_length=80, default="Жилой объект")
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    residents_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["address"]
        verbose_name = "Объект потребления"
        verbose_name_plural = "Объекты потребления"

    def __str__(self) -> str:
        return f"{self.address} ({self.consumer.full_name})"


class Contract(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Действует"
        SUSPENDED = "SUSPENDED", "Приостановлен"
        CLOSED = "CLOSED", "Закрыт"

    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="contracts")
    supply_object = models.ForeignKey(
        SupplyObject,
        on_delete=models.PROTECT,
        related_name="contracts",
    )
    number = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "number"]
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"

    def __str__(self) -> str:
        return self.number


class Meter(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Активен"
        REPLACED = "REPLACED", "Заменен"
        RETIRED = "RETIRED", "Выведен из эксплуатации"

    supply_object = models.ForeignKey(SupplyObject, on_delete=models.CASCADE, related_name="meters")
    serial_number = models.CharField(max_length=80, unique=True)
    model_name = models.CharField(max_length=120, blank=True)
    meter_type = models.CharField(max_length=80, default="Электросчетчик")
    install_date = models.DateField()
    commissioning_reading = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    multiplier = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal("1.000"))
    phase_count = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    replaced_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="replaced_meters",
    )

    class Meta:
        ordering = ["serial_number"]
        verbose_name = "Прибор учета"
        verbose_name_plural = "Приборы учета"

    def __str__(self) -> str:
        return self.serial_number


class MeterReading(models.Model):
    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Вручную"
        PHOTO = "PHOTO", "Фотография"
        CAMERA = "CAMERA", "Камера"
        EMPLOYEE = "EMPLOYEE", "Сотрудник"

    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Подтверждено"
        PENDING_REVIEW = "PENDING_REVIEW", "Ожидает проверки"
        REJECTED = "REJECTED", "Отклонено"

    class Meta:
        verbose_name = "Показание"
        verbose_name_plural = "Показания"
        ordering = ["-reading_date"]

    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.CASCADE,
        related_name="meter_readings",
    )
    meter = models.ForeignKey(
        Meter,
        on_delete=models.SET_NULL,
        related_name="readings",
        blank=True,
        null=True,
    )
    reading_date = models.DateField()
    value = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    photo = models.ImageField(upload_to="meter-readings/%Y/%m/", blank=True, null=True)
    recognized_value = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)
    recognition_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        blank=True,
        null=True,
    )
    review_comment = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.consumer.full_name} - {self.value} ({self.reading_date})"
