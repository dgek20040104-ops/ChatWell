import uuid

from django.conf import settings
from django.db import models


class Follow(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )

    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )

    is_accepted = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "follower",
                    "following",
                ],
                name="unique_follow_relation",
            ),
        ]

        ordering = [
            "-created_at",
        ]

    def __str__(self):
        status_text = (
            "подтверждена"
            if self.is_accepted
            else "ожидает подтверждения"
        )

        return (
            f"{self.follower} -> "
            f"{self.following} "
            f"({status_text})"
        )


class Post(models.Model):
    POST = "post"
    REEL = "reel"

    POST_TYPE_CHOICES = [
        (
            POST,
            "Публикация",
        ),
        (
            REEL,
            "Reel",
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
        related_name="posts",
    )

    text = models.TextField(
        max_length=5000,
        blank=True,
    )

    post_type = models.CharField(
        max_length=10,
        choices=POST_TYPE_CHOICES,
        default=POST,
    )

    is_pinned = models.BooleanField(
        default=False,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-is_pinned",
            "-created_at",
        ]

    def __str__(self):
        return f"Публикация {self.id}"


class PostMedia(models.Model):
    MEDIA_TYPES = (
        (
            "image",
            "Изображение",
        ),
        (
            "video",
            "Видео",
        ),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="media",
    )

    file = models.FileField(
        upload_to="posts/%Y/%m/%d/",
    )

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "created_at",
        ]

    def __str__(self):
        return (
            f"{self.media_type}: "
            f"{self.file.name}"
        )


class PostLike(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "post",
                    "user",
                ],
                name="unique_post_like",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user} likes "
            f"{self.post_id}"
        )


class Comment(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    text = models.TextField(
        max_length=1000,
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

    def __str__(self):
        return (
            f"Comment by "
            f"{self.author}"
        )


class SavedPost(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_posts",
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="saved_by_users",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "post",
                ],
                name="unique_saved_post",
            ),
        ]

        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.user} saved "
            f"{self.post_id}"
        )