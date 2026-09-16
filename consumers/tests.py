from decimal import Decimal
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from integrations.meter_ocr.fake import FakeMeterReadingRecognizer
from integrations.ml.anomaly_detector import ConsumptionAnomalyDetector

from .anomaly_services import detect_reading_anomaly
from .models import Consumer, Contract, Meter, MeterReading, SupplyObject
from .services import (
    create_consumer,
    import_camera_photo,
    recognize_photo_reading,
    review_meter_reading,
    submit_manual_reading,
)

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

    def test_consumer_dashboard_shows_only_linked_consumer(self, client):
        consumer_user = User.objects.create_user(
            username="linked_consumer",
            password="StrongPass123!",
            role=User.Role.CONSUMER,
        )
        consumer = Consumer.objects.create(
            user=consumer_user,
            account_number="A-2004",
            full_name="Связанный потребитель",
            address="ул. Личная, 1",
            contract_number="K-2004",
            tariff_rate=Decimal("5.00"),
        )
        Consumer.objects.create(
            account_number="A-2005",
            full_name="Другой потребитель",
            address="ул. Чужая, 2",
            contract_number="K-2005",
            tariff_rate=Decimal("5.00"),
        )

        client.force_login(consumer_user)
        response = client.get(reverse("consumer_dashboard"))

        assert response.status_code == 200
        assert consumer.full_name in response.content.decode()
        assert "Другой потребитель" not in response.content.decode()

    def test_manual_reading_lower_than_previous_waits_for_review(self):
        consumer = Consumer.objects.create(
            account_number="A-3002",
            full_name="Олег Соколов",
            address="ул. Тихая, 2",
            contract_number="K-3002",
            tariff_rate=Decimal("5.00"),
        )
        submit_manual_reading(
            consumer=consumer,
            reading_date="2026-08-01",
            value=Decimal("100.000"),
        )

        reading = submit_manual_reading(
            consumer=consumer,
            reading_date="2026-09-01",
            value=Decimal("90.000"),
        )

        assert reading.status == MeterReading.Status.PENDING_REVIEW
        assert reading.confirmed_at is None

    def test_duplicate_manual_reading_is_rejected(self):
        consumer = Consumer.objects.create(
            account_number="A-3003",
            full_name="Нина Белова",
            address="ул. Тихая, 3",
            contract_number="K-3003",
            tariff_rate=Decimal("5.00"),
        )
        submit_manual_reading(
            consumer=consumer,
            reading_date="2026-09-01",
            value=Decimal("100.000"),
        )

        with pytest.raises(ValidationError):
            submit_manual_reading(
                consumer=consumer,
                reading_date="2026-09-01",
                value=Decimal("100.000"),
            )

    def test_employee_can_review_manual_reading(self):
        consumer = Consumer.objects.create(
            account_number="A-3004",
            full_name="Роман Крылов",
            address="ул. Тихая, 4",
            contract_number="K-3004",
            tariff_rate=Decimal("5.00"),
        )
        submit_manual_reading(
            consumer=consumer,
            reading_date="2026-08-01",
            value=Decimal("100.000"),
        )
        reading = submit_manual_reading(
            consumer=consumer,
            reading_date="2026-09-01",
            value=Decimal("90.000"),
        )
        employee = User.objects.create_user(
            username="reviewer",
            password="StrongPass123!",
            role=User.Role.EMPLOYEE,
        )

        response = review_meter_reading(
            reading=reading,
            approved=True,
            reviewer=employee,
            comment="Проверено сотрудником",
        )

        assert response.status == MeterReading.Status.CONFIRMED
        assert response.review_comment == "Проверено сотрудником"

    def test_photo_reading_uses_fake_recognizer_and_stores_result(self):
        consumer = Consumer.objects.create(
            account_number="A-3005",
            full_name="Дарья Лебедева",
            address="ул. Тихая, 5",
            contract_number="K-3005",
            tariff_rate=Decimal("5.00"),
        )
        supply_object = SupplyObject.objects.create(consumer=consumer, address=consumer.address)
        meter = Meter.objects.create(
            supply_object=supply_object,
            serial_number="M-3005",
            install_date="2026-01-01",
        )
        image_buffer = BytesIO()
        Image.new("RGB", (20, 20), color="white").save(image_buffer, format="JPEG")
        photo = SimpleUploadedFile(
            "meter.jpg",
            image_buffer.getvalue(),
            content_type="image/jpeg",
        )

        reading = recognize_photo_reading(
            consumer=consumer,
            meter=meter,
            reading_date="2026-09-16",
            photo=photo,
            recognizer=FakeMeterReadingRecognizer(Decimal("123.450")),
        )

        assert reading.source == MeterReading.Source.PHOTO
        assert reading.recognized_value == Decimal("123.450")
        assert reading.status == MeterReading.Status.CONFIRMED

    def test_camera_photo_import_is_idempotent(self, tmp_path):
        consumer = Consumer.objects.create(
            account_number="A-3006",
            full_name="Евгений Морозов",
            address="ул. Тихая, 6",
            contract_number="K-3006",
            tariff_rate=Decimal("5.00"),
        )
        supply_object = SupplyObject.objects.create(consumer=consumer, address=consumer.address)
        meter = Meter.objects.create(
            supply_object=supply_object,
            serial_number="M-3006",
            install_date="2026-01-01",
        )
        image_path = Path(tmp_path) / "M-3006_2026-09-16.jpg"
        Image.new("RGB", (20, 20), color="white").save(image_path, format="JPEG")
        recognizer = FakeMeterReadingRecognizer(Decimal("222.000"))

        first = import_camera_photo(
            meter=meter,
            reading_date="2026-09-16",
            image_path=image_path,
            recognizer=recognizer,
        )
        second = import_camera_photo(
            meter=meter,
            reading_date="2026-09-16",
            image_path=image_path,
            recognizer=recognizer,
        )

        assert first is not None
        assert second is not None
        assert first.pk == second.pk
        assert MeterReading.objects.filter(photo_checksum=first.photo_checksum).count() == 1
        assert first.source == MeterReading.Source.CAMERA

    def test_anomaly_detector_requires_minimum_history(self):
        detector = ConsumptionAnomalyDetector()

        with pytest.raises(ValueError, match="Недостаточно данных"):
            detector.fit([[1.0, 0.0, 0.0, 1.0, 1.0, 30.0]])

    def test_anomaly_detector_trains_and_predicts(self):
        detector = ConsumptionAnomalyDetector()
        features = [[float(value), 1.0, 0.1, float(value), 1.0, 30.0] for value in range(5, 12)]

        metadata = detector.fit(features)
        prediction = detector.predict(features[-1])

        assert metadata["algorithm"] == "IsolationForest"
        assert prediction.is_anomaly is not None
        assert prediction.model_version == "isolation-forest-v1"

        with TemporaryDirectory() as directory:
            model_path = Path(directory) / "model.joblib"
            detector.save(model_path)
            assert model_path.exists()

    def test_anomaly_detection_stores_result(self):
        consumer = Consumer.objects.create(
            account_number="A-3007",
            full_name="Светлана Котова",
            address="ул. Тихая, 7",
            contract_number="K-3007",
            tariff_rate=Decimal("5.00"),
        )
        for index, value in enumerate(range(100, 108), start=1):
            MeterReading.objects.create(
                consumer=consumer,
                reading_date=f"2026-0{index}-01",
                value=Decimal(value),
            )
        reading = consumer.meter_readings.order_by("-reading_date").first()
        detector = ConsumptionAnomalyDetector()
        detector.fit([[float(value), 1.0, 0.1, float(value), 1.0, 30.0] for value in range(5, 12)])

        anomaly = detect_reading_anomaly(reading=reading, detector=detector)

        assert anomaly is not None
        assert anomaly.consumer == consumer
