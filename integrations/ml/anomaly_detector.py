from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURE_NAMES = [
    "consumption_kwh",
    "absolute_change",
    "relative_change",
    "rolling_mean_3",
    "month",
    "days_in_period",
]
MODEL_VERSION = "isolation-forest-v1"
MINIMUM_SAMPLES = 5


@dataclass(frozen=True)
class AnomalyPrediction:
    is_anomaly: bool | None
    score: Decimal | None
    model_version: str | None
    explanation: str


class ConsumptionAnomalyDetector:
    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path
        self.model: IsolationForest | None = None
        if model_path is not None and model_path.exists():
            self.model = joblib.load(model_path)

    def fit(self, features: list[list[float]]) -> dict[str, object]:
        if len(features) < MINIMUM_SAMPLES:
            raise ValueError("Недостаточно данных для обучения модели аномалий.")
        self.model = IsolationForest(n_estimators=100, contamination="auto", random_state=42)
        self.model.fit(np.asarray(features, dtype=float))
        return {
            "model_version": MODEL_VERSION,
            "feature_names": FEATURE_NAMES,
            "samples": len(features),
            "algorithm": "IsolationForest",
        }

    def save(self, path: Path) -> None:
        if self.model is None:
            raise ValueError("Модель еще не обучена.")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def predict(self, features: list[float]) -> AnomalyPrediction:
        if self.model is None:
            return AnomalyPrediction(None, None, None, "Модель аномалий еще не обучена.")
        values = np.asarray([features], dtype=float)
        is_anomaly = bool(self.model.predict(values)[0] == -1)
        score = Decimal(str(float(-self.model.score_samples(values)[0]))).quantize(
            Decimal("0.00001")
        )
        explanation = (
            "Обнаружено нетипичное потребление, требуется проверка."
            if is_anomaly
            else "Показание соответствует обученному профилю потребления."
        )
        return AnomalyPrediction(is_anomaly, score, MODEL_VERSION, explanation)
