import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_FOLLOW = "follow"
    TYPE_LIKE = "like"
    TYPE_COMMENT = "comment"
    TYPE_MESSAGE = "message"
    TYPE_FOLLOW_REQUEST = "follow_request"

    TYPE_CHOICES = [
        (
            TYPE_FOLLOW,
            "Новая подписка",
        ),
        (
            TYPE_LIKE,
            "Лайк",
        ),
        (
            TYPE_COMMENT,
            "Комментарий",
        ),
        (
            TYPE_MESSAGE,
            "Сообщение",
        ),
        (
            TYPE_FOLLOW_REQUEST,
            "Запрос на подписку",
        ),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_notifications",
        null=True,
        blank=True,
    )

    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
    )

    text = models.CharField(
        max_length=255,
        blank=True,
    )

    post_id = models.UUIDField(
        null=True,
        blank=True,
    )

    chat_id = models.UUIDField(
        null=True,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "recipient",
                    "is_read",
                ],
            ),
            models.Index(
                fields=[
                    "recipient",
                    "created_at",
                ],
            ),
        ]

    def __str__(self):
        return (
            f"{self.notification_type}: "
            f"{self.recipient_id}"
        )