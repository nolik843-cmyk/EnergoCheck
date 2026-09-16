from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RecognitionResult:
    value: Decimal | None
    confidence: Decimal
    raw_text: str
    backend: str
    diagnostic: str = ""


class MeterReadingRecognizer(Protocol):
    def recognize(self, image_path: Path) -> RecognitionResult:
        """Распознает показание прибора и возвращает результат без изменения БД."""
