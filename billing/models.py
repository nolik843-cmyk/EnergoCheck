from __future__ import annotations

from decimal import Decimal

from django.db import models

from consumers.models import Consumer


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        ISSUED = "ISSUED", "Выставлен"
        PAID = "PAID", "Оплачен"
        OVERDUE = "OVERDUE", "Просрочен"

    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    billing_period = models.CharField(max_length=20)
    previous_reading = models.DecimalField(max_digits=12, decimal_places=3)
    current_reading = models.DecimalField(max_digits=12, decimal_places=3)
    consumption_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.00"))
    tariff_rate = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.00"))
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

    def save(self, *args, **kwargs):
        if self.consumption_kwh == Decimal("0.00"):
            self.consumption_kwh = self.current_reading - self.previous_reading
        if self.total_amount == Decimal("0.00"):
            self.total_amount = (self.consumption_kwh * self.tariff_rate).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.consumer.full_name} / {self.billing_period} / {self.total_amount}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Наличные"
        CARD = "CARD", "Карта"
        TRANSFER = "TRANSFER", "Перевод"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.TRANSFER,
    )
    reference = models.CharField(max_length=80, unique=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at"]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"

    def __str__(self) -> str:
        return f"{self.invoice.consumer.full_name} — {self.amount}"
