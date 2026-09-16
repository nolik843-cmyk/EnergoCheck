from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from consumers.anomaly_services import build_anomaly_features
from consumers.models import MeterReading
from integrations.ml.anomaly_detector import ConsumptionAnomalyDetector


class Command(BaseCommand):
    help = "Обучает IsolationForest для поиска нетипичного потребления."

    def handle(self, *args, **options) -> None:
        features = build_anomaly_features(MeterReading.objects.all())
        detector = ConsumptionAnomalyDetector()
        try:
            metadata = detector.fit(features)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        model_path = Path(settings.ML_MODELS_DIR) / "consumption_anomaly.joblib"
        metadata_path = model_path.with_suffix(".json")
        detector.save(model_path)
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.stdout.write(self.style.SUCCESS(f"Модель сохранена: {model_path}"))
