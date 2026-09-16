from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CONSUMER = "CONSUMER", "Потребитель"
        EMPLOYEE = "EMPLOYEE", "Сотрудник"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CONSUMER,
        db_index=True,
    )

    @property
    def is_consumer(self) -> bool:
        return self.role == self.Role.CONSUMER

    @property
    def is_employee(self) -> bool:
        return self.role == self.Role.EMPLOYEE

    class Meta:
        db_table = "auth_user"
