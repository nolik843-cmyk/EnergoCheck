from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .base import RecognitionResult


class EasyOCRMeterReadingRecognizer:
    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = languages or ["en"]
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            import easyocr

            self._reader = easyocr.Reader(self.languages, gpu=False, verbose=False)
        return self._reader

    def recognize(self, image_path: Path) -> RecognitionResult:
        if not image_path.is_file():
            return RecognitionResult(
                value=None,
                confidence=Decimal("0"),
                raw_text="",
                backend="easyocr",
                diagnostic="Файл изображения не найден.",
            )

        try:
            results = self._get_reader().readtext(
                str(image_path),
                allowlist="0123456789.,",
                detail=1,
            )
        except Exception as exc:
            return RecognitionResult(
                value=None,
                confidence=Decimal("0"),
                raw_text="",
                backend="easyocr",
                diagnostic=f"Ошибка OCR: {exc.__class__.__name__}",
            )

        candidates: list[tuple[Decimal, Decimal, str]] = []
        for _box, text, confidence in results:
            normalized = re.sub(r"[^0-9.,]", "", text).replace(",", ".")
            if not normalized:
                continue
            try:
                value = Decimal(normalized)
                score = Decimal(str(max(0.0, min(1.0, float(confidence)))))
            except (InvalidOperation, ValueError):
                continue
            candidates.append((score, value, text))

        if not candidates:
            return RecognitionResult(
                value=None,
                confidence=Decimal("0"),
                raw_text="",
                backend="easyocr",
                diagnostic="Цифровое показание не найдено.",
            )

        score, value, raw_text = max(candidates, key=lambda item: item[0])
        return RecognitionResult(
            value=value,
            confidence=score.quantize(Decimal("0.0001")),
            raw_text=raw_text,
            backend="easyocr",
        )
