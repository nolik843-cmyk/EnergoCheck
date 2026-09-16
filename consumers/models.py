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


class MeterReading(models.Model):
    class Meta:
        verbose_name = "Показание"
        verbose_name_plural = "Показания"
        ordering = ["-reading_date"]

    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.CASCADE,
        related_name="meter_readings",
    )
    reading_date = models.DateField()
    value = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.consumer.full_name} - {self.value} ({self.reading_date})"
