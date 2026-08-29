from django.contrib import admin
from .models import Comment
from .models import Follow
from .models import Post
from .models import PostLike
from .models import PostMedia
from .models import SavedPost


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "post",
        "created_at",
    )

    search_fields = (
        "user__phone",
        "user__username",
        "post__text",
    )

    list_filter = (
        "created_at",
    )

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "text",
        "is_archived",
        "created_at",
    )

    list_filter = (
        "is_archived",
        "created_at",
    )

    search_fields = (
        "text",
        "author__phone",
        "author__username",
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        "follower",
        "following",
        "created_at",
    )

    search_fields = (
        "follower__phone",
        "following__phone",
    )

@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "media_type",
        "file_size",
        "created_at",
    )

    list_filter = (
        "media_type",
        "created_at",
    )

    search_fields = (
        "file",
        "post__text",
    )

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = (
        "post",
        "user",
        "created_at",
    )

    search_fields = (
        "user__phone",
        "user__username",
        "post__text",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "post",
        "author",
        "text",
        "created_at",
    )

    search_fields = (
        "text",
        "author__phone",
        "author__username",
        "post__text",
    )

    list_filter = (
        "created_at",
    )