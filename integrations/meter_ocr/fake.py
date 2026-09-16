from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from .base import RecognitionResult


class FakeMeterReadingRecognizer:
    def __init__(self, value: Decimal | None, confidence: Decimal = Decimal("0.99")) -> None:
        self.value = value
        self.confidence = confidence

    def recognize(self, image_path: Path) -> RecognitionResult:
        return RecognitionResult(
            value=self.value,
            confidence=self.confidence,
            raw_text=str(self.value) if self.value is not None else "",
            backend="fake",
            diagnostic=f"Тестовый файл: {image_path.name}",
        )
