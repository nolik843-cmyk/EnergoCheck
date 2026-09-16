from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

User = get_user_model()


def create_user_with_role(**kwargs: Any) -> User:
    role = kwargs.pop("role", User.Role.CONSUMER)
    return User.objects.create_user(role=role, **kwargs)
