from rest_framework import serializers

from .models import Notification


class NotificationActorSerializer(
    serializers.Serializer
):
    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_id(self, obj):
        return getattr(
            obj,
            "pk",
            None,
        )

    def get_username(self, obj):
        return getattr(
            obj,
            "username",
            None,
        )

    def get_display_name(self, obj):
        return getattr(
            obj,
            "display_name",
            None,
        )

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
        except (
            AttributeError,
            ValueError,
        ):
            return None

        request = self.context.get(
            "request",
        )

        if request is not None:
            return request.build_absolute_uri(
                url,
            )

        return url


class NotificationSerializer(
    serializers.ModelSerializer
):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = Notification

        fields = [
            "id",
            "actor",
            "notification_type",
            "text",
            "post_id",
            "chat_id",
            "is_read",
            "created_at",
        ]

        read_only_fields = fields

    def get_actor(self, obj):
        actor = getattr(
            obj,
            "actor",
            None,
        )

        if actor is None:
            return None

        return NotificationActorSerializer(
            actor,
            context=self.context,
        ).data