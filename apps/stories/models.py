import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Story(models.Model):
    MEDIA_IMAGE = "image"
    MEDIA_VIDEO = "video"

    MEDIA_CHOICES = [
        (
            MEDIA_IMAGE,
            "Изображение",
        ),
        (
            MEDIA_VIDEO,
            "Видео",
        ),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories",
    )

    media = models.FileField(
    upload_to="stories/%Y/%m/%d/",
    blank=True,
    null=True,
)

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_CHOICES,
    )

    text = models.TextField(
        max_length=500,
        blank=True,
    )

    decorations = models.JSONField(
        default=list,
        blank=True,
    )

    allow_reactions = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "author",
                    "expires_at",
                ],
            ),
            models.Index(
                fields=[
                    "expires_at",
                ],
            ),
        ]

    def is_active(self):
        return self.expires_at > timezone.now()

    def __str__(self):
        return (
            f"История {self.author_id} "
            f"от {self.created_at}"
        )


class StoryView(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="story_views",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="viewed_stories",
    )

    viewed_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "story",
                    "user",
                ],
                name="unique_story_view",
            ),
        ]

    def __str__(self):
        return (
            f"Просмотр {self.user_id} "
            f"истории {self.story_id}"
        )


class StoryReaction(models.Model):
    HEART = "heart"
    LAUGH = "laugh"
    LOVE = "love"
    WOW = "wow"
    SAD = "sad"
    FIRE = "fire"

    REACTION_CHOICES = [
        (
            HEART,
            "❤️",
        ),
        (
            LAUGH,
            "😂",
        ),
        (
            LOVE,
            "😍",
        ),
        (
            WOW,
            "😮",
        ),
        (
            SAD,
            "😢",
        ),
        (
            FIRE,
            "🔥",
        ),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="reactions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_reactions",
    )

    reaction = models.CharField(
        max_length=20,
        choices=REACTION_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "story",
                    "user",
                ],
                name="unique_story_user_reaction",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user_id} "
            f"{self.reaction} "
            f"{self.story_id}"
        )