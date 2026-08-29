from rest_framework import serializers

from .models import Story


class StoryAuthorSerializer(
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
            "request",
        )

        if request is not None:
            return request.build_absolute_uri(url)

        return url


class StorySerializer(
    serializers.ModelSerializer
):
    author = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()
    views_count = serializers.IntegerField(
        read_only=True,
    )
    reactions_count = serializers.IntegerField(
        read_only=True,
    )
    my_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            "id",
            "author",
            "media_url",
            "media_type",
            "text",
            "decorations",
            "allow_reactions",
            "created_at",
            "expires_at",
            "views_count",
            "reactions_count",
            "my_reaction",
        ]
        read_only_fields = fields

    def get_author(self, obj):
        return StoryAuthorSerializer(
            obj.author,
            context=self.context,
        ).data

    def get_media_url(self, obj):
        media = getattr(
            obj,
            "media",
            None,
        )

        if not media:
            return None

        try:
            url = media.url
        except ValueError:
            return None

        request = self.context.get(
            "request",
        )

        if request is not None:
            return request.build_absolute_uri(url)

        return url

    def get_views_count(self, obj):
        return getattr(
            obj,
            "views_count",
            0,
        )

    def get_reactions_count(self, obj):
        return getattr(
            obj,
            "reactions_count",
            0,
        )

    def get_my_reaction(self, obj):
        request = self.context.get(
            "request",
        )

        if request is None:
            return None

        user = getattr(
            request,
            "user",
            None,
        )

        if user is None or not user.is_authenticated:
            return None

        reaction = (
            obj.reactions
            .filter(user=user)
            .values_list(
                "reaction",
                flat=True,
            )
            .first()
        )

        return reaction