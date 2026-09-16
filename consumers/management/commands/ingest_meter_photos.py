from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from consumers.models import Meter
from consumers.services import import_camera_photo
from integrations.meter_ocr.easyocr_adapter import EasyOCRMeterReadingRecognizer
from integrations.meter_ocr.fake import FakeMeterReadingRecognizer


class Command(BaseCommand):
    help = "Импортирует фотографии показаний счетчиков из папки."
    filename_pattern = re.compile(
        r"^(?P<serial>[A-Za-z0-9_-]+)_(?P<date>\d{4}-\d{2}-\d{2})\.[A-Za-z0-9]+$"
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("folder", type=Path)
        parser.add_argument(
            "--backend",
            choices=["fake", "easyocr"],
            default="fake",
            help="OCR backend для импорта.",
        )

    def handle(self, *args, **options) -> None:
        folder: Path = options["folder"]
        if not folder.is_dir():
            raise CommandError(f"Папка не найдена: {folder}")

        recognizer = (
            EasyOCRMeterReadingRecognizer()
            if options["backend"] == "easyocr"
            else FakeMeterReadingRecognizer(None)
        )
        imported = 0
        skipped = 0
        for image_path in sorted(folder.iterdir()):
            if not image_path.is_file():
                continue
            match = self.filename_pattern.match(image_path.name)
            if match is None:
                self.stdout.write(f"Пропущен файл с неверным именем: {image_path.name}")
                skipped += 1
                continue
            meter = Meter.objects.filter(serial_number=match["serial"]).first()
            if meter is None:
                self.stdout.write(f"Счетчик не найден: {match['serial']}")
                skipped += 1
                continue
            reading = import_camera_photo(
                meter=meter,
                reading_date=date.fromisoformat(match["date"]),
                image_path=image_path,
                recognizer=recognizer,
            )
            if reading is None:
                skipped += 1
            else:
                imported += 1

        self.stdout.write(self.style.SUCCESS(f"Импортировано: {imported}; пропущено: {skipped}."))
