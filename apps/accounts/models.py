import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
)
from django.contrib.auth.models import (
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(
    AbstractBaseUser,
    PermissionsMixin,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    phone = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
    )

    username = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    display_name = models.CharField(
        max_length=100,
        blank=True,
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
    )

    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        null=True,
        blank=True,
    )

    is_phone_verified = models.BooleanField(
        default=False,
    )

    is_verified = models.BooleanField(
    default=False,
)
    
    is_private = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    last_seen = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_online = models.BooleanField(
        default=False,
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone

    def mark_online(self):
        self.is_online = True
        self.last_seen = timezone.now()

        self.save(
            update_fields=[
                "is_online",
                "last_seen",
            ]
        )

    def mark_offline(self):
        self.is_online = False
        self.last_seen = timezone.now()

        self.save(
            update_fields=[
                "is_online",
                "last_seen",
            ]
        )


class VerificationCode(
    models.Model
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    phone = models.CharField(
        max_length=20,
        db_index=True,
    )

    code_hash = models.CharField(
        max_length=128,
    )

    attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(
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
                    "phone",
                    "-created_at",
                ],
            ),
        ]

    def is_expired(self):
        return timezone.now() >= self.expires_at
