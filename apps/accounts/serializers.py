import re


from django.core.validators import (
    validate_image_file_extension,
)


from rest_framework import serializers


from .models import User


PHONE_PATTERN = re.compile(
    r"^\+[0-9]{9,19}$"
)


USERNAME_PATTERN = re.compile(
    r"^[A-Za-z0-9_]{3,30}$"
)


def normalize_phone(
    value,
):
    """
    Разрешённый формат номера:

        +79991234567

    Номера без символа + отклоняются.
    """

    value = str(
        value or ""
    ).strip()

    value = value.replace(
        " ",
        "",
    )

    value = value.replace(
        "-",
        "",
    )

    value = value.replace(
        "(",
        "",
    )

    value = value.replace(
        ")",
        "",
    )

    return value


def normalize_username(
    value,
):
    """
    Поддерживает:

        alex
        @alex

    В базе хранится:

        alex
    """

    value = str(
        value or ""
    ).strip()

    if value.startswith("@"):
        value = value[1:]

    return value


class RequestCodeSerializer(
    serializers.Serializer
):
    phone = serializers.CharField(
        max_length=30,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    def validate_phone(
        self,
        value,
    ):
        value = normalize_phone(
            value
        )

        if not value.startswith("+"):
            raise serializers.ValidationError(
                (
                    "Номер должен начинаться "
                    "с символа +. Пример: "
                    "+79991234567."
                )
            )

        if not PHONE_PATTERN.fullmatch(
            value
        ):
            raise serializers.ValidationError(
                (
                    "Введите корректный номер, "
                    "например +79991234567."
                )
            )

        return value


class VerifyCodeSerializer(
    serializers.Serializer
):
    phone = serializers.CharField(
        max_length=30,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    code = serializers.CharField(
        min_length=6,
        max_length=6,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    username = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
    )

    display_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
    )

    def validate_phone(
        self,
        value,
    ):
        value = normalize_phone(
            value
        )

        if not value.startswith("+"):
            raise serializers.ValidationError(
                (
                    "Номер должен начинаться "
                    "с символа +. Пример: "
                    "+79991234567."
                )
            )

        if not PHONE_PATTERN.fullmatch(
            value
        ):
            raise serializers.ValidationError(
                (
                    "Введите корректный номер, "
                    "например +79991234567."
                )
            )

        return value

    def validate_code(
        self,
        value,
    ):
        value = str(
            value or ""
        ).strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Код должен содержать только цифры."
            )

        if len(value) != 6:
            raise serializers.ValidationError(
                "Код должен содержать ровно 6 цифр."
            )

        return value

    def validate_username(
        self,
        value,
    ):
        if value is None:
            return ""

        value = normalize_username(
            value
        )

        if not value:
            return ""

        if not USERNAME_PATTERN.fullmatch(
            value
        ):
            raise serializers.ValidationError(
                (
                    "Тег должен содержать от 3 до "
                    "30 символов: латинские буквы, "
                    "цифры и символ _."
                )
            )

        return value

    def validate_display_name(
        self,
        value,
    ):
        if value is None:
            return ""

        return str(
            value
        ).strip()


class UserSerializer(
    serializers.ModelSerializer
):
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[
            validate_image_file_extension,
        ],
    )

    followers_count = (
        serializers.SerializerMethodField()
    )

    following_count = (
        serializers.SerializerMethodField()
    )

    MAX_AVATAR_SIZE = (
        10 * 1024 * 1024
    )

    ALLOWED_AVATAR_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    class Meta:
        model = User

        fields = (
            "id",
            "phone",
            "username",
            "display_name",
            "bio",
            "avatar",
            "is_verified",
            "is_phone_verified",
            "is_verified",
            "is_private",
            "followers_count",
            "following_count",
            "created_at",
            "last_seen",
        )

        read_only_fields = (
            "id",
            "phone",
            "is_phone_verified",
            "is_verified",
            "followers_count",
            "following_count",
            "created_at",
            "last_seen",
        )

        extra_kwargs = {
            "username": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "display_name": {
                "required": False,
                "allow_blank": True,
            },
            "bio": {
                "required": False,
                "allow_blank": True,
            },
            "is_private": {
                "required": False,
            },
        }

    def get_followers_count(
        self,
        obj,
    ):
        return obj.follower_relations.filter(
            is_accepted=True,
        ).count()

    def get_following_count(
        self,
        obj,
    ):
        return obj.following_relations.filter(
            is_accepted=True,
        ).count()

    def validate_avatar(
        self,
        value,
    ):
        if value is None:
            return value

        if value.size > self.MAX_AVATAR_SIZE:
            raise serializers.ValidationError(
                "Аватарка не должна быть больше 10 МБ."
            )

        content_type = (
            value.content_type or ""
        ).lower()

        if content_type not in (
            self.ALLOWED_AVATAR_TYPES
        ):
            raise serializers.ValidationError(
                "Разрешены только JPG, PNG и WEBP."
            )

        return value

    def validate_username(
        self,
        value,
    ):
        if value is None:
            return None

        value = normalize_username(
            value
        )

        if not value:
            return None

        if not USERNAME_PATTERN.fullmatch(
            value
        ):
            raise serializers.ValidationError(
                (
                    "Тег должен содержать от 3 до "
                    "30 символов: латинские буквы, "
                    "цифры и символ _."
                )
            )

        queryset = User.objects.filter(
            username__iexact=value,
        )

        if self.instance is not None:
            queryset = queryset.exclude(
                id=self.instance.id,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "Пользователь с таким тегом уже существует."
            )

        return value

    def validate_display_name(
        self,
        value,
    ):
        if value is None:
            return ""

        return str(
            value
        ).strip()

    def validate_bio(
        self,
        value,
    ):
        if value is None:
            return ""

        return str(
            value
        ).strip()


class PublicUserSerializer(
    serializers.ModelSerializer
):
    followers_count = serializers.IntegerField(
        read_only=True,
    )

    following_count = serializers.IntegerField(
        read_only=True,
    )

    is_following = serializers.BooleanField(
        read_only=True,
    )

    is_pending = serializers.BooleanField(
        read_only=True,
    )

    avatar = serializers.ImageField(
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = User

        fields = (
            "id",
            "username",
            "display_name",
            "bio",
            "avatar",
            "is_verified",
            "is_private",
            "followers_count",
            "following_count",
            "is_following",
            "is_pending",
        )

        read_only_fields = fields
