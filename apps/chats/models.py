import uuid

from django.conf import settings
from django.db import models


class Chat(models.Model):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"

    CHAT_TYPES = (
        (PRIVATE, "Личный чат"),
        (GROUP, "Группа"),
        (CHANNEL, "Сообщество"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    chat_type = models.CharField(
        max_length=20,
        choices=CHAT_TYPES,
        default=PRIVATE,
    )

    title = models.CharField(
        max_length=150,
        blank=True,
    )

    description = models.TextField(
        max_length=1000,
        blank=True,
    )

    avatar = models.ImageField(
        upload_to="chats/avatars/%Y/%m/",
        null=True,
        blank=True,
    )

    is_public = models.BooleanField(
        default=False,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_chats",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-updated_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "chat_type",
                    "updated_at",
                ],
            ),
            models.Index(
                fields=[
                    "is_public",
                    "chat_type",
                ],
            ),
        ]

    def __str__(self):
        return self.title or f"Чат {self.id}"


class ChatMember(models.Model):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"

    ROLES = (
        (MEMBER, "Участник"),
        (ADMIN, "Администратор"),
        (OWNER, "Владелец"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default=MEMBER,
    )

    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "chat",
                    "user",
                ],
                name="unique_chat_member",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "chat",
                    "user",
                ],
            ),
            models.Index(
                fields=[
                    "user",
                    "last_read_at",
                ],
            ),
        ]

    def __str__(self):
        return f"{self.user} в {self.chat}"


class Message(models.Model):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    SHARED_POST = "shared_post"

    MESSAGE_TYPES = (
        (
            TEXT,
            "Текст",
        ),
        (
            IMAGE,
            "Изображение",
        ),
        (
            VIDEO,
            "Видео",
        ),
        (
            FILE,
            "Файл",
        ),
        (
            SHARED_POST,
            "Публикация",
        ),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default=TEXT,
    )

    text = models.TextField(
        max_length=5000,
        blank=True,
    )

    file = models.FileField(
        upload_to="chats/files/%Y/%m/%d/",
        null=True,
        blank=True,
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
    )

    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
    )

    shared_post = models.ForeignKey(
        "posts.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shared_chat_messages",
    )

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    is_edited = models.BooleanField(
        default=False,
    )

    is_deleted = models.BooleanField(
        default=False,
    )

    is_delivered = models.BooleanField(
        default=False,
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="read_chat_messages",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "chat",
                    "created_at",
                ],
            ),
            models.Index(
                fields=[
                    "chat",
                    "is_deleted",
                    "created_at",
                ],
            ),
            models.Index(
                fields=[
                    "message_type",
                    "created_at",
                ],
            ),
        ]

    def __str__(self):
        return f"{self.sender} в {self.chat}"