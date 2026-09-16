from __future__ import annotations

from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def create_notification(
    user: User | None,
    title: str,
    message: str,
    kind: str = Notification.Type.INFO,
) -> Notification:
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=kind,
    )
