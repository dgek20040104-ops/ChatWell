from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, VerificationCode


@admin.register(User)
class ChatWellUserAdmin(UserAdmin):
    model = User

    list_display = (
        "phone",
        "username",
        "display_name",
        "is_phone_verified",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_phone_verified",
        "is_active",
        "is_staff",
        "is_private",
    )

    search_fields = (
        "phone",
        "username",
        "display_name",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "phone",
                    "password",
                ),
            },
        ),
        (
            "Профиль",
            {
                "fields": (
                    "username",
                    "display_name",
                    "bio",
                    "avatar",
                ),
            },
        ),
        (
            "Права и безопасность",
            {
                "fields": (
                    "is_phone_verified",
                    "is_private",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Даты",
            {
                "fields": (
                    "last_login",
                    "last_seen",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "last_seen",
    )


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "attempts",
        "expires_at",
        "is_used",
        "created_at",
    )

    search_fields = ("phone",)
    list_filter = ("is_used",)
    readonly_fields = ("code_hash",)