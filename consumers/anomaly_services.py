from __future__ import annotations

from decimal import Decimal

from django.db.models import QuerySet
from django.utils import timezone

from integrations.ml.anomaly_detector import ConsumptionAnomalyDetector

from .models import ConsumptionAnomaly, MeterReading


def build_anomaly_features(readings: QuerySet[MeterReading]) -> list[list[float]]:
    confirmed = list(
        readings.filter(status=MeterReading.Status.CONFIRMED)
        .order_by("reading_date", "created_at")
        .only("reading_date", "value")
    )
    features: list[list[float]] = []
    previous_value: Decimal | None = None
    history: list[Decimal] = []
    for reading in confirmed:
        consumption = (
            reading.value - previous_value if previous_value is not None else reading.value
        )
        absolute_change = abs(consumption - history[-1]) if history else Decimal("0")
        relative_change = absolute_change / history[-1] if history and history[-1] else Decimal("0")
        rolling = history[-3:] + [consumption]
        features.append(
            [
                float(consumption),
                float(absolute_change),
                float(relative_change),
                float(sum(rolling, Decimal("0")) / len(rolling)),
                float(reading.reading_date.month),
                float(max(reading.reading_date.day, 1)),
            ]
        )
        previous_value = reading.value
        history.append(consumption)
    return features


def build_reading_features(reading: MeterReading) -> list[float]:
    features = build_anomaly_features(reading.consumer.meter_readings.all())
    return features[-1] if features else []


def detect_reading_anomaly(
    *, reading: MeterReading, detector: ConsumptionAnomalyDetector
) -> ConsumptionAnomaly | None:
    features = build_reading_features(reading)
    prediction = detector.predict(features) if features else None
    if prediction is None or prediction.is_anomaly is None or prediction.score is None:
        return None
    return ConsumptionAnomaly.objects.create(
        consumer=reading.consumer,
        meter=reading.meter,
        reading=reading,
        period=reading.reading_date,
        anomaly_score=prediction.score,
        description=prediction.explanation,
        model_version=prediction.model_version or "unknown",
        detected_at=timezone.now(),
    )
