from django.core.exceptions import ValidationError

from .models import Notification


def create_notification(
    recipient,
    actor=None,
    notification_type="",
    text="",
    post_id=None,
    chat_id=None,
):
    """
    Создаёт уведомление.

    Не создаёт уведомление:
    - если отсутствует получатель;
    - если пользователь уведомляет сам себя;
    - если передан неизвестный тип уведомления.
    """

    if recipient is None:
        return None

    if actor is not None and recipient.pk == actor.pk:
        return None

    valid_types = {
        notification_type_value
        for notification_type_value, _ in Notification.TYPE_CHOICES
    }

    if notification_type not in valid_types:
        raise ValidationError(
            {
                "notification_type": (
                    f"Недопустимый тип уведомления: "
                    f"{notification_type}"
                )
            }
        )

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        text=text or "",
        post_id=post_id,
        chat_id=chat_id,
    )