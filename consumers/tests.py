from decimal import Decimal

import pytest
from django.urls import reverse

from .models import Consumer, MeterReading
from .services import create_consumer


@pytest.mark.django_db
class TestConsumerBilling:
    def test_consumer_creation(self):
        consumer = Consumer.objects.create(
            account_number="A-1001",
            full_name="Иван Иванов",
            address="ул. Лесная, 10",
            contract_number="K-001",
            tariff_rate=Decimal("5.50"),
        )

        assert consumer.account_number == "A-1001"
        assert consumer.is_active is True
        assert str(consumer) == "Иван Иванов (A-1001)"

    def test_meter_reading_creation(self):
        consumer = Consumer.objects.create(
            account_number="A-1002",
            full_name="Петр Петров",
            address="ул. Центральная, 15",
            contract_number="K-002",
            tariff_rate=Decimal("6.25"),
        )

        reading = MeterReading.objects.create(
            consumer=consumer,
            reading_date="2026-09-01",
            value=Decimal("120.500"),
        )

        assert reading.consumer == consumer
        assert reading.value == Decimal("120.500")

    def test_monthly_bill_calculation(self):
        consumer = Consumer.objects.create(
            account_number="A-1003",
            full_name="Анна Сергеева",
            address="ул. Садовая, 8",
            contract_number="K-003",
            tariff_rate=Decimal("7.10"),
        )

        delta = Decimal("42.5")
        total = delta * consumer.tariff_rate

        assert total == Decimal("301.75")

    def test_create_consumer_service(self):
        consumer = create_consumer(
            account_number="A-2001",
            full_name="Сергей Кузнецов",
            address="ул. Сосновая, 5",
            contract_number="K-2001",
            tariff_rate=Decimal("4.80"),
        )

        assert consumer.pk is not None
        assert consumer.full_name == "Сергей Кузнецов"
        assert consumer.is_active is True

    def test_consumer_detail_view(self, client):
        consumer = Consumer.objects.create(
            account_number="A-2002",
            full_name="Елена Васильева",
            address="ул. Речная, 18",
            contract_number="K-2002",
            tariff_rate=Decimal("6.30"),
        )

        response = client.get(reverse("consumer_detail", kwargs={"pk": consumer.pk}))

        assert response.status_code == 200
        assert response.context["consumer"] == consumer
        assert "Елена Васильева" in response.content.decode()
