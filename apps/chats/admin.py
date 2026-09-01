from django.contrib import admin


from .models import Chat
from .models import ChatMember
from .models import Message


@admin.register(Chat)
class ChatAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "chat_type",
        "title",
        "owner",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "chat_type",
        "is_public",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "owner__phone",
        "owner__username",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(ChatMember)
class ChatMemberAdmin(
    admin.ModelAdmin
):
    list_display = (
        "chat",
        "user",
        "role",
        "last_read_at",
        "joined_at",
    )

    list_filter = (
        "role",
        "joined_at",
    )

    search_fields = (
        "user__phone",
        "user__username",
        "chat__title",
    )

    readonly_fields = (
        "id",
        "joined_at",
    )

    list_select_related = (
        "chat",
        "user",
    )


@admin.register(Message)
class MessageAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "chat",
        "sender",
        "message_type",
        "is_edited",
        "is_deleted",
        "is_delivered",
        "created_at",
    )

    list_filter = (
        "message_type",
        "is_edited",
        "is_deleted",
        "is_delivered",
        "created_at",
    )

    search_fields = (
        "text",
        "file_name",
        "sender__phone",
        "sender__username",
        "chat__title",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "chat",
        "sender",
    )
