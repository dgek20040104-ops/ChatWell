from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import serializers

from .models import Chat
from .models import ChatMember
from .models import Message


User = get_user_model()


class ChatUserSerializer(
    serializers.Serializer
):
    id = serializers.UUIDField(
        read_only=True,
    )

    username = serializers.CharField(
        read_only=True,
        allow_null=True,
    )

    display_name = serializers.CharField(
        read_only=True,
        allow_null=True,
    )

    avatar = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        avatar = getattr(
            obj,
            "avatar",
            None,
        )

        if not avatar:
            return None

        try:
            url = avatar.url
        except ValueError:
            return None

        request = self.context.get(
            "request"
        )

        if request is not None:
            return request.build_absolute_uri(
                url
            )

        return url

    def get_is_online(self, obj):
        return bool(
            getattr(
                obj,
                "is_online",
                False,
            )
        )


class UserSearchSerializer(
    ChatUserSerializer
):
    pass


class MessageSerializer(
    serializers.ModelSerializer
):
    sender = ChatUserSerializer(
        read_only=True,
    )

    reply_to = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()

    class Meta:
        model = Message

        fields = (
            "id",
            "chat",
            "sender",
            "message_type",
            "text",
            "file",
            "file_name",
            "file_size",
            "mime_type",
            "reply_to",
            "is_edited",
            "is_deleted",
            "is_delivered",
            "delivered_at",
            "read_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "chat",
            "sender",
            "message_type",
            "file",
            "file_name",
            "file_size",
            "mime_type",
            "reply_to",
            "is_edited",
            "is_deleted",
            "is_delivered",
            "delivered_at",
            "read_count",
            "created_at",
            "updated_at",
        )

    def get_file(self, obj):
        if not obj.file:
            return None

        try:
            url = obj.file.url
        except ValueError:
            return None

        request = self.context.get(
            "request"
        )

        if request is not None:
            return request.build_absolute_uri(
                url
            )

        return url

    def get_reply_to(self, obj):
        reply = obj.reply_to

        if reply is None:
            return None

        return {
            "id": str(reply.id),
            "sender_id": str(
                reply.sender_id
            ),
            "text": (
                "Сообщение удалено"
                if reply.is_deleted
                else reply.text
            ),
        }

    def get_read_count(self, obj):
        if not hasattr(
            obj,
            "read_by"
        ):
            return 0

        return obj.read_by.count()


class CreateFileMessageSerializer(
    serializers.Serializer
):
    file = serializers.FileField(
        required=True,
    )

    text = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        default="",
    )

    reply_to = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
    )

    MAX_FILE_SIZE = 100 * 1024 * 1024

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    }

    VIDEO_EXTENSIONS = {
        ".mp4",
        ".webm",
        ".mov",
        ".avi",
    }

    FILE_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".zip",
        ".rar",
        ".txt",
    }

    IMAGE_MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    VIDEO_MIME_TYPES = {
        "video/mp4",
        "video/webm",
        "video/quicktime",
        "video/x-msvideo",
    }

    FILE_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/zip",
        "application/x-rar-compressed",
        "application/vnd.rar",
        "application/vnd.ms-excel",
        (
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
        (
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        "text/plain",
    }

    def validate_file(self, value):
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                "Размер файла не может превышать 100 МБ."
            )

        file_name = value.name.lower()

        if "." not in file_name:
            raise serializers.ValidationError(
                "У файла отсутствует расширение."
            )

        extension = (
            "."
            + file_name.rsplit(
                ".",
                1,
            )[1]
        )

        allowed_extensions = (
            self.IMAGE_EXTENSIONS
            | self.VIDEO_EXTENSIONS
            | self.FILE_EXTENSIONS
        )

        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                "Этот тип файла не поддерживается."
            )

        content_type = (
            value.content_type or ""
        ).lower()

        allowed_mime_types = (
            self.IMAGE_MIME_TYPES
            | self.VIDEO_MIME_TYPES
            | self.FILE_MIME_TYPES
        )

        if content_type not in allowed_mime_types:
            raise serializers.ValidationError(
                "Недопустимый MIME-тип файла."
            )

        extension_group_is_correct = (
            (
                extension in self.IMAGE_EXTENSIONS
                and content_type
                in self.IMAGE_MIME_TYPES
            )
            or (
                extension in self.VIDEO_EXTENSIONS
                and content_type
                in self.VIDEO_MIME_TYPES
            )
            or (
                extension in self.FILE_EXTENSIONS
                and content_type
                in self.FILE_MIME_TYPES
            )
        )

        if not extension_group_is_correct:
            raise serializers.ValidationError(
                "Расширение файла не соответствует его типу."
            )

        return value

    def validate_text(self, value):
        return (value or "").strip()


class CreateMessageSerializer(
    serializers.ModelSerializer
):
    reply_to = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Message

        fields = (
            "text",
            "reply_to",
        )

    def validate_text(self, value):
        value = (value or "").strip()

        if not value:
            raise serializers.ValidationError(
                "Сообщение не может быть пустым."
            )

        if len(value) > 5000:
            raise serializers.ValidationError(
                "Сообщение не может быть длиннее "
                "5000 символов."
            )

        return value


class ChatMemberSerializer(
    serializers.ModelSerializer
):
    user = ChatUserSerializer(
        read_only=True,
    )

    class Meta:
        model = ChatMember

        fields = (
            "id",
            "user",
            "role",
            "last_read_at",
            "joined_at",
        )

        read_only_fields = fields


class ChatSerializer(
    serializers.ModelSerializer
):
    avatar = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat

        fields = (
            "id",
            "chat_type",
            "title",
            "description",
            "avatar",
            "is_public",
            "other_user",
            "last_message",
            "members_count",
            "my_role",
            "unread_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_unread_count(self, obj):
        request = self.context.get(
            "request"
        )

        if (
            request is None
            or not request.user.is_authenticated
        ):
            return 0

        membership = (
            obj.members
            .filter(
                user=request.user,
            )
            .first()
        )

        if membership is None:
            return 0

        messages = (
            obj.messages
            .filter(
                is_deleted=False,
            )
            .exclude(
                sender=request.user,
            )
        )

        if membership.last_read_at is not None:
            messages = messages.filter(
                created_at__gt=membership.last_read_at,
            )

        return messages.count()

    def get_avatar(self, obj):
        avatar = getattr(
            obj,
            "avatar",
            None,
        )

        if not avatar:
            return None

        try:
            url = avatar.url
        except ValueError:
            return None

        request = self.context.get(
            "request"
        )

        if request is not None:
            return request.build_absolute_uri(
                url
            )

        return url

    def get_other_user(self, obj):
        if obj.chat_type != Chat.PRIVATE:
            return None

        request = self.context.get(
            "request"
        )

        if request is None:
            return None

        member = (
            obj.members
            .exclude(
                user=request.user,
            )
            .select_related(
                "user",
            )
            .first()
        )

        if member is None:
            return None

        return ChatUserSerializer(
            member.user,
            context=self.context,
        ).data

    def get_last_message(self, obj):
        message = (
            obj.messages
            .filter(
                is_deleted=False,
            )
            .select_related(
                "sender",
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        if message is None:
            return None

        return {
            "id": str(message.id),
            "text": message.text,
            "message_type": (
                message.message_type
            ),
            "file_name": (
                message.file_name
            ),
            "sender_id": str(
                message.sender_id
            ),
            "created_at": (
                message.created_at
            ),
        }

    def get_members_count(self, obj):
        return obj.members.count()

    def get_my_role(self, obj):
        request = self.context.get(
            "request"
        )

        if request is None:
            return None

        membership = (
            obj.members
            .filter(
                user=request.user,
            )
            .first()
        )

        if membership is None:
            return None

        return membership.role


class CreatePrivateChatSerializer(
    serializers.Serializer
):
    username = serializers.CharField(
        max_length=50,
    )

    def validate_username(self, value):
        request = self.context.get(
            "request"
        )

        username = (
            value.strip()
            .lstrip("@")
        )

        if not username:
            raise serializers.ValidationError(
                "Введите тег пользователя."
            )

        if request is not None:
            current_username = (
                request.user.username or ""
            )

            if (
                current_username.lower()
                == username.lower()
            ):
                raise serializers.ValidationError(
                    "Нельзя создать чат с самим собой."
                )

        if not User.objects.filter(
            username__iexact=username,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "Пользователь не найден."
            )

        return username


class CreateGroupSerializer(
    serializers.Serializer
):
    title = serializers.CharField(
        max_length=150,
    )

    description = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
    )

    usernames = serializers.ListField(
        child=serializers.CharField(
            max_length=50,
        ),
        required=False,
        allow_empty=True,
    )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Введите название группы."
            )

        return value

    def validate_usernames(self, value):
        result = []
        seen = set()

        for username in value:
            username = (
                username
                .strip()
                .lstrip("@")
            )
            key = username.lower()

            if username and key not in seen:
                result.append(username)
                seen.add(key)

        return result


class CreateChannelSerializer(
    serializers.Serializer
):
    title = serializers.CharField(
        max_length=150,
    )

    description = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
    )

    is_public = serializers.BooleanField(
        required=False,
        default=True,
    )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Введите название сообщества."
            )

        return value


class AddMemberSerializer(
    serializers.Serializer
):
    username = serializers.CharField(
        max_length=50,
    )

    def validate_username(self, value):
        value = (
            value
            .strip()
            .lstrip("@")
        )

        if not value:
            raise serializers.ValidationError(
                "Введите тег пользователя."
            )

        user = (
            User.objects
            .filter(
                username__iexact=value,
                is_active=True,
            )
            .first()
        )

        if user is None:
            raise serializers.ValidationError(
                "Пользователь не найден."
            )

        self.user_object = user

        return value