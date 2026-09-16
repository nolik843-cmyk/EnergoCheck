from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Consumer, Contract, Meter, MeterReading, SupplyObject
from .services import create_consumer

User = get_user_model()


@pytest.mark.django_db
class TestConsumerBilling:
    def test_supply_object_contract_and_meter_relationships(self):
        consumer = Consumer.objects.create(
            account_number="A-3001",
            full_name="Ирина Орлова",
            address="ул. Новая, 1",
            contract_number="K-3001",
            tariff_rate=Decimal("5.00"),
        )
        supply_object = SupplyObject.objects.create(
            consumer=consumer,
            address="ул. Новая, 1",
            object_type="Квартира",
            area_m2=Decimal("54.20"),
            residents_count=2,
        )
        contract = Contract.objects.create(
            consumer=consumer,
            supply_object=supply_object,
            number="DOG-3001",
            start_date="2026-01-01",
        )
        meter = Meter.objects.create(
            supply_object=supply_object,
            serial_number="M-3001",
            install_date="2026-01-01",
        )

        assert contract.supply_object == supply_object
        assert meter.supply_object == supply_object
        assert list(consumer.supply_objects.all()) == [supply_object]

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

    def test_consumer_detail_view_requires_employee_login(self, client):
        consumer = Consumer.objects.create(
            account_number="A-2002",
            full_name="Елена Васильева",
            address="ул. Речная, 18",
            contract_number="K-2002",
            tariff_rate=Decimal("6.30"),
        )

        response = client.get(reverse("consumer_detail", kwargs={"pk": consumer.pk}))

        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_employee_can_open_consumer_detail(self, client):
        employee = User.objects.create_user(
            username="employee_detail",
            password="StrongPass123!",
            role=User.Role.EMPLOYEE,
        )
        consumer = Consumer.objects.create(
            account_number="A-2003",
            full_name="Елена Васильева",
            address="ул. Речная, 18",
            contract_number="K-2003",
            tariff_rate=Decimal("6.30"),
        )

        client.force_login(employee)
        response = client.get(reverse("consumer_detail", kwargs={"pk": consumer.pk}))

        assert response.status_code == 200
        assert response.context["consumer"] == consumer
        assert "Елена Васильева" in response.content.decode()

    def test_consumer_role_cannot_open_employee_page(self, client):
        consumer_user = User.objects.create_user(
            username="consumer_detail",
            password="StrongPass123!",
            role=User.Role.CONSUMER,
        )

        client.force_login(consumer_user)
        response = client.get(reverse("consumer_list"))

        assert response.status_code == 302
        assert response["Location"] == "/accounts/login/?next=/consumers/"
