from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse

from consumers.models import Consumer, Contract, Meter, SupplyObject
from employee.forms import ContractForm, MeterForm

User = get_user_model()


@pytest.fixture
def consumers(db):
    first = Consumer.objects.create(
        account_number="STAGE1-A", full_name="Первый", address="Адрес 1",
        contract_number="STAGE1-C1", tariff_rate=Decimal("5.00"),
    )
    second = Consumer.objects.create(
        account_number="STAGE1-B", full_name="Второй", address="Адрес 2",
        contract_number="STAGE1-C2", tariff_rate=Decimal("5.00"),
    )
    return first, second


@pytest.mark.django_db
def test_contract_cannot_reference_another_consumers_object(consumers):
    first, second = consumers
    obj = SupplyObject.objects.create(consumer=second, address="Адрес 2")
    contract = Contract(
        consumer=first, supply_object=obj, number="INVALID-C1",
        start_date=date(2026, 1, 1),
    )
    with pytest.raises(ValidationError):
        contract.full_clean()


@pytest.mark.django_db
def test_contract_date_range_is_validated(consumers):
    first, _ = consumers
    obj = SupplyObject.objects.create(consumer=first, address="Адрес 1")
    form = ContractForm(data={
        "consumer": first.pk, "supply_object": obj.pk, "number": "BAD-DATE",
        "start_date": "2026-12-01", "end_date": "2026-01-01", "status": "ACTIVE",
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_meter_rejects_nonpositive_multiplier(consumers):
    first, _ = consumers
    obj = SupplyObject.objects.create(consumer=first, address="Адрес 1")
    form = MeterForm(data={
        "supply_object": obj.pk, "serial_number": "STAGE1-M",
        "model_name": "", "meter_type": "Электросчётчик",
        "install_date": "2026-01-01", "commissioning_reading": "0",
        "multiplier": "0", "phase_count": 1, "status": "ACTIVE",
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_unlinked_consumer_dashboard_does_not_crash(client):
    user = User.objects.create_user(
        username="unlinked_stage1", password="StrongPass123!",
        role=User.Role.CONSUMER,
    )
    client.force_login(user)
    assert client.get(reverse("consumer_dashboard")).status_code == 404


@pytest.mark.django_db
def test_staff_can_search_and_edit_consumer(client, consumers):
    first, second = consumers
    employee = User.objects.create_user(
        username="stage1_employee", password="StrongPass123!",
        role=User.Role.EMPLOYEE,
    )
    client.force_login(employee)
    response = client.get(reverse("consumer_list"), {"q": "STAGE1-A"})
    assert response.status_code == 200
    assert first in response.context["consumers"]
    assert second not in response.context["consumers"]
    response = client.get(reverse("consumer_edit", kwargs={"pk": first.pk}))
    assert response.status_code == 200


@pytest.mark.django_db
def test_consumer_cannot_edit_staff_catalogues(client, consumers):
    first, _ = consumers
    user = User.objects.create_user(
        username="stage1_consumer", password="StrongPass123!",
        role=User.Role.CONSUMER,
    )
    first.user = user
    first.save(update_fields=["user"])
    client.force_login(user)
    assert client.get(reverse("consumer_edit", kwargs={"pk": first.pk})).status_code == 302
