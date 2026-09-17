from __future__ import annotations

from decimal import Decimal

from django.db import models

from consumers.models import Consumer, Contract


class Tariff(models.Model):
    name = models.CharField(max_length=120)
    price_per_kwh = models.DecimalField(max_digits=10, decimal_places=4)
    valid_from = models.DateField()
    valid_to = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_from", "name"]
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def __str__(self) -> str:
        return f"{self.name} ({self.price_per_kwh})"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        ISSUED = "ISSUED", "Выставлен"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Частично оплачен"
        PAID = "PAID", "Оплачен"
        OVERDUE = "OVERDUE", "Просрочен"

    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name="invoices",
        blank=True,
        null=True,
    )
    billing_period = models.CharField(max_length=20)
    previous_reading = models.DecimalField(max_digits=12, decimal_places=3)
    current_reading = models.DecimalField(max_digits=12, decimal_places=3)
    consumption_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.00"))
    tariff_rate = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.00"))
    tariff_name_snapshot = models.CharField(max_length=120, blank=True)
    price_per_kwh_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ISSUED,
    )
    due_date = models.DateField()
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-billing_period", "-issued_at"]
        verbose_name = "Счёт"
        verbose_name_plural = "Счета"
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "billing_period"],
                name="unique_contract_billing_period",
            )
        ]

    def save(self, *args, **kwargs):
        if self.consumption_kwh == Decimal("0.00"):
            self.consumption_kwh = self.current_reading - self.previous_reading
        if self.total_amount == Decimal("0.00"):
            self.total_amount = (self.consumption_kwh * self.tariff_rate).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.consumer.full_name} / {self.billing_period} / {self.total_amount}"


class Payment(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Успешно"
        FAILED = "FAILED", "Ошибка"

    class Method(models.TextChoices):
        DEMO = "DEMO", "Демо-оплата"
        CASH = "CASH", "Наличные"
        CARD = "CARD", "Карта"
        TRANSFER = "TRANSFER", "Перевод"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    payment_method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.TRANSFER,
    )
    reference = models.CharField(max_length=80, unique=True)
    demo_reference = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_payments",
    )
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at"]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"

    def __str__(self) -> str:
        return f"{self.invoice.consumer.full_name} — {self.amount}"
