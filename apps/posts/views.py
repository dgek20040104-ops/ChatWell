from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

from rest_framework import status
from rest_framework.parsers import FormParser
from rest_framework.parsers import JSONParser
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment
from .models import Follow
from .models import Post
from .models import PostLike
from .models import PostMedia
from .models import SavedPost
from .serializers import CommentSerializer
from .serializers import CreateCommentSerializer
from .serializers import CreatePostSerializer
from .serializers import PostSerializer


User = get_user_model()


def posts_queryset():
    """
    Общий queryset для публикаций.

    Загружает связанные объекты заранее,
    чтобы избежать большого количества SQL-запросов
    при сериализации.
    """

    return (
        Post.objects
        .select_related("author")
        .prefetch_related(
            "media",
            "likes",
            "comments",
            "saved_by_users",
        )
    )


def user_avatar_url(user, request):
    """
    Возвращает URL аватара пользователя.

    Если request передан, возвращается абсолютный URL.
    """

    avatar = getattr(
        user,
        "avatar",
        None,
    )

    if not avatar:
        return None

    try:
        url = avatar.url
    except ValueError:
        return None

    if request is not None:
        return request.build_absolute_uri(url)

    return url


def serialize_user(user, request):
    """
    Формирует краткую информацию о пользователе.
    """

    return {
        "id": str(user.id),
        "username": getattr(
            user,
            "username",
            None,
        ),
        "display_name": getattr(
            user,
            "display_name",
            None,
        ),
        "avatar": user_avatar_url(
            user,
            request,
        ),
    }


class CreatePostView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    MAX_FILES = 10

    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    MAX_VIDEO_SIZE = 100 * 1024 * 1024

    ALLOWED_IMAGE_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    ALLOWED_VIDEO_TYPES = {
        "video/mp4",
        "video/webm",
        "video/quicktime",
    }

    def post(self, request):
        serializer = CreatePostSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        uploaded_files = request.FILES.getlist(
            "media",
        )

        text = serializer.validated_data.get(
            "text",
            "",
        )

        text = (text or "").strip()

        post_type = serializer.validated_data.get(
            "post_type",
            Post.POST,
        )

        if post_type not in {
            Post.POST,
            Post.REEL,
        }:
            return Response(
                {
                    "detail": (
                        "Недопустимый тип публикации."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not text and not uploaded_files:
            return Response(
                {
                    "detail": (
                        "Добавьте текст, фотографию "
                        "или видео."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(uploaded_files) > self.MAX_FILES:
            return Response(
                {
                    "detail": (
                        "Можно загрузить максимум "
                        f"{self.MAX_FILES} файлов."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_video = False

        for uploaded_file in uploaded_files:
            content_type = (
                uploaded_file.content_type or ""
            ).lower()

            file_size = uploaded_file.size
            extension = Path(
                uploaded_file.name,
            ).suffix.lower()

            if not extension:
                return Response(
                    {
                        "detail": (
                            "Файл должен иметь "
                            "расширение."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if content_type in self.ALLOWED_IMAGE_TYPES:
                if file_size > self.MAX_IMAGE_SIZE:
                    return Response(
                        {
                            "detail": (
                                "Размер изображения "
                                "не может превышать "
                                "10 МБ."
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            elif content_type in self.ALLOWED_VIDEO_TYPES:
                has_video = True

                if file_size > self.MAX_VIDEO_SIZE:
                    return Response(
                        {
                            "detail": (
                                "Размер видео не "
                                "может превышать "
                                "100 МБ."
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            else:
                return Response(
                    {
                        "detail": (
                            "Разрешены только JPG, "
                            "PNG, WEBP, MP4, WEBM "
                            "и MOV."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if post_type == Post.REEL:
            if len(uploaded_files) != 1:
                return Response(
                    {
                        "detail": (
                            "Reel должен содержать "
                            "ровно один видеофайл."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            first_file = uploaded_files[0]
            first_content_type = (
                first_file.content_type or ""
            ).lower()

            if first_content_type not in (
                self.ALLOWED_VIDEO_TYPES
            ):
                return Response(
                    {
                        "detail": (
                            "Reel может содержать "
                            "только видео."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if post_type == Post.POST and not has_video:
            post_type = Post.POST

        with transaction.atomic():
            post = serializer.save(
                author=request.user,
                post_type=post_type,
            )

            for uploaded_file in uploaded_files:
                content_type = (
                    uploaded_file.content_type or ""
                ).lower()

                if content_type in (
                    self.ALLOWED_IMAGE_TYPES
                ):
                    media_type = "image"
                else:
                    media_type = "video"

                PostMedia.objects.create(
                    post=post,
                    file=uploaded_file,
                    media_type=media_type,
                    file_size=uploaded_file.size,
                )

        post = (
            posts_queryset()
            .get(id=post.id)
        )

        return Response(
            PostSerializer(
                post,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
        )


class FeedView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        following_ids = (
            Follow.objects
            .filter(
                follower=request.user,
                is_accepted=True,
            )
            .values_list(
                "following_id",
                flat=True,
            )
        )

        posts = (
            posts_queryset()
            .filter(
                Q(author=request.user)
                | Q(author_id__in=following_ids),
                is_archived=False,
            )
        )

        serializer = PostSerializer(
            posts,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class ReelsFeedView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        reels = (
            posts_queryset()
            .filter(
                post_type=Post.REEL,
                is_archived=False,
            )
            .order_by(
                "-created_at",
            )
        )

        serializer = PostSerializer(
            reels,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class MyPostsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        posts = (
    posts_queryset()
    .filter(
        author=request.user,
        is_archived=False,
        media__isnull=False,
    )
    .distinct()
)

        serializer = PostSerializer(
            posts,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class SavedPostsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        posts = (
            posts_queryset()
            .filter(
                saved_by_users__user=request.user,
                is_archived=False,
            )
            .distinct()
        )

        serializer = PostSerializer(
            posts,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UserPostsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, user_id):
        try:
            user = User.objects.get(
                id=user_id,
                is_active=True,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Пользователь не найден."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        is_owner = request.user.id == user.id

        relation = (
            Follow.objects
            .filter(
                follower=request.user,
                following=user,
            )
            .first()
        )

        is_following = bool(
            relation and relation.is_accepted
        )

        is_pending = bool(
            relation and not relation.is_accepted
        )

        is_private = bool(
            getattr(
                user,
                "is_private",
                False,
            )
        )

        can_view = (
            is_owner
            or not is_private
            or is_following
        )

        if not can_view:
            return Response(
                {
                    "is_private": is_private,
                    "can_view": False,
                    "is_following": False,
                    "is_pending": is_pending,
                    "posts_count": 0,
                    "posts": [],
                },
                status=status.HTTP_200_OK,
            )

        posts = (
    posts_queryset()
    .filter(
        author=user,
        is_archived=False,
        media__isnull=False,
    )
    .distinct()
)

        followers_count = (
            Follow.objects
            .filter(
                following=user,
                is_accepted=True,
            )
            .count()
        )

        following_count = (
            Follow.objects
            .filter(
                follower=user,
                is_accepted=True,
            )
            .count()
        )

        serializer = PostSerializer(
            posts,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "is_private": is_private,
                "can_view": True,
                "is_following": is_following,
                "is_pending": is_pending,
                "posts_count": posts.count(),
                "followers_count": followers_count,
                "following_count": following_count,
                "posts": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class DeletePostView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                author=request.user,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        post.is_archived = True
        post.save(
            update_fields=[
                "is_archived",
                "updated_at",
            ],
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class FollowUserView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, user_id):
        if request.user.id == user_id:
            return Response(
                {
                    "detail": (
                        "Нельзя подписаться "
                        "на самого себя."
                    ),
                    "is_following": False,
                    "is_pending": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.get(
                id=user_id,
                is_active=True,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "detail": "Пользователь не найден.",
                    "is_following": False,
                    "is_pending": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        relation = (
            Follow.objects
            .filter(
                follower=request.user,
                following=target_user,
            )
            .first()
        )

        if relation is not None:
            if relation.is_accepted:
                return Response(
                    {
                        "detail": "Вы уже подписаны.",
                        "is_following": True,
                        "is_pending": False,
                        "is_accepted": True,
                        "follow_id": str(
                            relation.id,
                        ),
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "detail": (
                        "Запрос уже отправлен "
                        "и ожидает подтверждения."
                    ),
                    "is_following": False,
                    "is_pending": True,
                    "is_accepted": False,
                    "follow_id": str(
                        relation.id,
                    ),
                },
                status=status.HTTP_200_OK,
            )

        is_private = bool(
            getattr(
                target_user,
                "is_private",
                False,
            )
        )

        relation = Follow.objects.create(
            follower=request.user,
            following=target_user,
            is_accepted=not is_private,
        )

        if is_private:
            return Response(
                {
                    "detail": (
                        "Запрос на подписку отправлен."
                    ),
                    "is_following": False,
                    "is_pending": True,
                    "is_accepted": False,
                    "follow_id": str(
                        relation.id,
                    ),
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(
            {
                "detail": "Вы подписались.",
                "is_following": True,
                "is_pending": False,
                "is_accepted": True,
                "follow_id": str(
                    relation.id,
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class UnfollowUserView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, user_id):
        deleted_count, _ = (
            Follow.objects
            .filter(
                follower=request.user,
                following_id=user_id,
            )
            .delete()
        )

        if deleted_count == 0:
            return Response(
                {
                    "detail": (
                        "Подписка или запрос "
                        "не найдены."
                    ),
                    "is_following": False,
                    "is_pending": False,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "detail": (
                    "Подписка или запрос удалены."
                ),
                "is_following": False,
                "is_pending": False,
            },
            status=status.HTTP_200_OK,
        )

class FollowRequestsView(APIView):
    """
    Возвращает входящие запросы
    на подписку текущего пользователя.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        requests = (
            Follow.objects
            .filter(
                following=request.user,
                is_accepted=False,
            )
            .select_related(
                "follower",
            )
            .order_by(
                "-created_at",
            )
        )

        result = []

        for relation in requests:
            follower = relation.follower

            result.append(
                {
                    "id": str(relation.id),
                    "follow_id": str(relation.id),
                    "user": serialize_user(
                        follower,
                        request,
                    ),
                    "follower": serialize_user(
                        follower,
                        request,
                    ),
                    "created_at": relation.created_at,
                    "is_pending": True,
                    "is_accepted": False,
                }
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class AcceptFollowRequestView(APIView):
    """
    Принимает запрос на подписку.

    Владелец профиля может принять
    только запрос, адресованный ему.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def post(self, request, follow_id):
        try:
            relation = (
                Follow.objects
                .select_related(
                    "follower",
                    "following",
                )
                .get(
                    id=follow_id,
                    following=request.user,
                )
            )
        except Follow.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Запрос на подписку "
                        "не найден."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if relation.is_accepted:
            return Response(
                {
                    "detail": (
                        "Этот запрос уже принят."
                    ),
                    "follow_id": str(
                        relation.id,
                    ),
                    "is_following": True,
                    "is_pending": False,
                    "is_accepted": True,
                },
                status=status.HTTP_200_OK,
            )

        relation.is_accepted = True

        relation.save(
            update_fields=[
                "is_accepted",
            ],
        )

        return Response(
            {
                "detail": (
                    "Запрос на подписку принят."
                ),
                "follow_id": str(
                    relation.id,
                ),
                "follower": serialize_user(
                    relation.follower,
                    request,
                ),
                "is_following": True,
                "is_pending": False,
                "is_accepted": True,
            },
            status=status.HTTP_200_OK,
        )


class RejectFollowRequestView(APIView):
    """
    Отклоняет и удаляет запрос
    на подписку текущего пользователя.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def delete(self, request, follow_id):
        try:
            relation = Follow.objects.get(
                id=follow_id,
                following=request.user,
                is_accepted=False,
            )
        except Follow.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Ожидающий запрос "
                        "не найден."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        relation.delete()

        return Response(
            {
                "detail": (
                    "Запрос на подписку отклонён."
                ),
                "follow_id": str(
                    follow_id,
                ),
                "is_following": False,
                "is_pending": False,
                "is_accepted": False,
            },
            status=status.HTTP_200_OK,
        )

class FollowersView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        followers = (
            User.objects
            .filter(
                follower_relations__following=request.user,
                follower_relations__is_accepted=True,
                is_active=True,
            )
            .distinct()
        )

        return Response(
            [
                serialize_user(
                    user,
                    request,
                )
                for user in followers
            ],
            status=status.HTTP_200_OK,
        )


class FollowingView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        following = (
            User.objects
            .filter(
                following_relations__follower=request.user,
                following_relations__is_accepted=True,
                is_active=True,
            )
            .distinct()
        )

        return Response(
            [
                serialize_user(
                    user,
                    request,
                )
                for user in following
            ],
            status=status.HTTP_200_OK,
        )


class LikePostView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        like, created = (
            PostLike.objects.get_or_create(
                post=post,
                user=request.user,
            )
        )

        if not created:
            return Response(
                {
                    "detail": "Вы уже поставили лайк.",
                    "liked": True,
                    "likes_count": (
                        PostLike.objects
                        .filter(post=post)
                        .count()
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "liked": True,
                "likes_count": (
                    PostLike.objects
                    .filter(post=post)
                    .count()
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class UnlikePostView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_count, _ = (
            PostLike.objects
            .filter(
                post=post,
                user=request.user,
            )
            .delete()
        )

        if deleted_count == 0:
            return Response(
                {
                    "detail": "Лайк не найден.",
                    "liked": False,
                    "likes_count": (
                        PostLike.objects
                        .filter(post=post)
                        .count()
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "liked": False,
                "likes_count": (
                    PostLike.objects
                    .filter(post=post)
                    .count()
                ),
            },
            status=status.HTTP_200_OK,
        )


class PostCommentsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, post_id):
        try:
            Post.objects.get(
                id=post_id,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        comments = (
            Comment.objects
            .filter(
                post_id=post_id,
            )
            .select_related(
                "author",
            )
        )

        serializer = CommentSerializer(
            comments,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CreateCommentSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        comment = serializer.save(
            post=post,
            author=request.user,
        )

        comment = (
            Comment.objects
            .select_related("author")
            .get(id=comment.id)
        )

        return Response(
            CommentSerializer(
                comment,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DeleteCommentView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, comment_id):
        try:
            comment = Comment.objects.get(
                id=comment_id,
                author=request.user,
            )
        except Comment.DoesNotExist:
            return Response(
                {
                    "detail": "Комментарий не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        comment.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class SavePostView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        saved_post, created = (
            SavedPost.objects.get_or_create(
                user=request.user,
                post=post,
            )
        )

        return Response(
            {
                "saved": True,
                "already_saved": not created,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, post_id):
        deleted_count, _ = (
            SavedPost.objects
            .filter(
                user=request.user,
                post_id=post_id,
            )
            .delete()
        )

        if deleted_count == 0:
            return Response(
                {
                    "detail": (
                        "Публикация не была сохранена."
                    ),
                    "saved": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "saved": False,
            },
            status=status.HTTP_200_OK,
        )


class PinPostView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                author=request.user,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if post.is_pinned:
            return Response(
                {
                    "detail": (
                        "Публикация уже закреплена."
                    ),
                    "is_pinned": True,
                },
                status=status.HTTP_200_OK,
            )

        pinned_count = (
            Post.objects
            .filter(
                author=request.user,
                is_pinned=True,
                is_archived=False,
            )
            .count()
        )

        if pinned_count >= 3:
            return Response(
                {
                    "detail": (
                        "Можно закрепить максимум "
                        "3 публикации."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        post.is_pinned = True
        post.save(
            update_fields=[
                "is_pinned",
                "updated_at",
            ],
        )

        return Response(
            {
                "is_pinned": True,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(
                id=post_id,
                author=request.user,
                is_archived=False,
            )
        except Post.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Публикация не найдена."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not post.is_pinned:
            return Response(
                {
                    "detail": (
                        "Публикация не закреплена."
                    ),
                    "is_pinned": False,
                },
                status=status.HTTP_200_OK,
            )

        post.is_pinned = False
        post.save(
            update_fields=[
                "is_pinned",
                "updated_at",
            ],
        )

        return Response(
            {
                "is_pinned": False,
            },
            status=status.HTTP_200_OK,
        )