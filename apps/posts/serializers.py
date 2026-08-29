from rest_framework import serializers

from .models import Comment
from .models import Follow
from .models import Post
from .models import PostLike
from .models import PostMedia


class AuthorSerializer(
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
            return request.build_absolute_uri(
                url,
            )

        return url


class PostMediaSerializer(
    serializers.ModelSerializer
):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = (
            "id",
            "url",
            "media_type",
            "file_size",
            "created_at",
        )
        read_only_fields = fields

    def get_url(self, obj):
        file_field = getattr(
            obj,
            "file",
            None,
        )

        if not file_field:
            return None

        try:
            url = file_field.url
        except ValueError:
            return None

        request = self.context.get(
            "request",
        )

        if request is not None:
            return request.build_absolute_uri(
                url,
            )

        return url

class PostSerializer(
    serializers.ModelSerializer
):
    author = AuthorSerializer(
        read_only=True,
    )

    media = PostMediaSerializer(
        many=True,
        read_only=True,
    )

    likes_count = serializers.IntegerField(
        source="likes.count",
        read_only=True,
    )

    comments_count = serializers.IntegerField(
        source="comments.count",
        read_only=True,
    )

    liked_by_me = serializers.SerializerMethodField()
    saved_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "text",
            "post_type",
            "is_pinned",
            "is_archived",
            "media",
            "likes_count",
            "comments_count",
            "liked_by_me",
            "saved_by_me",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "is_archived",
            "media",
            "likes_count",
            "comments_count",
            "liked_by_me",
            "saved_by_me",
            "created_at",
            "updated_at",
        )

    def _get_request_user(self):
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

        return user

    def get_liked_by_me(self, obj):
        user = self._get_request_user()

        if user is None:
            return False

        return obj.likes.filter(
            user=user,
        ).exists()

    def get_saved_by_me(self, obj):
        user = self._get_request_user()

        if user is None:
            return False

        return obj.saved_by_users.filter(
            user=user,
        ).exists()


class CreatePostSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Post

        fields = (
            "text",
            "post_type",
        )

        extra_kwargs = {
            "text": {
                "required": False,
                "allow_blank": True,
            },
            "post_type": {
                "required": False,
            },
        }

    def validate_text(self, value):
        return (value or "").strip()


class FollowSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Follow
        fields = (
            "id",
            "follower",
            "following",
            "is_accepted",
            "created_at",
        )
        read_only_fields = (
            "id",
            "follower",
            "is_accepted",
            "created_at",
        )


class CommentSerializer(
    serializers.ModelSerializer
):
    author = AuthorSerializer(
        read_only=True
    )

    class Meta:
        model = Comment

        fields = (
            "id",
            "author",
            "text",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "author",
            "created_at",
            "updated_at",
        )


class CreateCommentSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Comment

        fields = (
            "text",
        )

    def validate_text(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Комментарий не может быть пустым."
            )

        return value


class PostLikeSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = PostLike

        fields = (
            "id",
            "post",
            "user",
            "created_at",
        )

        read_only_fields = (
            "id",
            "post",
            "user",
            "created_at",
        )