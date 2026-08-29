import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser
from rest_framework.parsers import JSONParser
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Follow

from .models import Story
from .models import StoryReaction
from .models import StoryView
from .serializers import StorySerializer


MAX_STORY_FILE_SIZE = 50 * 1024 * 1024
MAX_DECORATIONS = 30


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}


def stories_queryset():
    """
    Общий queryset для историй.

    Загружает автора и количество просмотров/реакций
    заранее, чтобы уменьшить количество SQL-запросов.
    """

    return (
        Story.objects
        .select_related("author")
        .annotate(
            views_count=Count(
                "story_views",
                distinct=True,
            ),
            reactions_count=Count(
                "reactions",
                distinct=True,
            ),
        )
    )


def get_active_story(story_id):
    """
    Возвращает активную историю или None.
    """

    return (
        stories_queryset()
        .filter(
            id=story_id,
            expires_at__gt=timezone.now(),
        )
        .first()
    )


def user_can_access_story(user, story):
    """
    Проверяет, может ли пользователь просматривать историю.

    История доступна:
    - автору;
    - пользователю, который подписан на автора,
      если подписка подтверждена.
    """

    if user.id == story.author_id:
        return True

    return Follow.objects.filter(
        follower=user,
        following_id=story.author_id,
        is_accepted=True,
    ).exists()


def story_not_found_response():
    return Response(
        {
            "detail": "История не найдена.",
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def parse_decorations(raw_decorations):
    """
    Преобразует decorations из multipart/form-data
    или JSON в список.

    Поддерживаются варианты:

    - decorations='[]'
    - decorations='[{"type": "text"}]'
    - decorations=[{"type": "text"}]
    """

    if raw_decorations in (
        None,
        "",
    ):
        return []

    if isinstance(raw_decorations, list):
        decorations = raw_decorations

    elif isinstance(raw_decorations, str):
        try:
            decorations = json.loads(
                raw_decorations,
            )
        except json.JSONDecodeError:
            raise ValueError(
                "Поле decorations должно "
                "содержать корректный JSON."
            )

    else:
        raise ValueError(
            "Поле decorations должно быть списком."
        )

    if not isinstance(decorations, list):
        raise ValueError(
            "Поле decorations должно быть списком."
        )

    if len(decorations) > MAX_DECORATIONS:
        raise ValueError(
            f"Максимум {MAX_DECORATIONS} "
            "элементов оформления."
        )

    return decorations


class StoryListView(APIView):
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

        author_ids = list(following_ids)
        author_ids.append(request.user.id)

        stories = (
            stories_queryset()
            .filter(
                author_id__in=author_ids,
                expires_at__gt=timezone.now(),
            )
            .order_by(
                "author_id",
                "-created_at",
            )
        )

        serializer = StorySerializer(
            stories,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class StoryCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def post(self, request):
        media = request.FILES.get(
            "media",
        )

        if media is None:
            return Response(
                {
                    "detail": (
                        "Для истории необходимо "
                        "добавить фото или видео."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        text = str(
            request.data.get(
                "text",
                "",
            )
        ).strip()

        if len(text) > 500:
            return Response(
                {
                    "detail": (
                        "Текст не может быть "
                        "длиннее 500 символов."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        content_type = (
            getattr(
                media,
                "content_type",
                "",
            )
            or ""
        ).lower()

        if content_type in ALLOWED_IMAGE_TYPES:
            media_type = Story.MEDIA_IMAGE

        elif content_type in ALLOWED_VIDEO_TYPES:
            media_type = Story.MEDIA_VIDEO

        else:
            return Response(
                {
                    "detail": (
                        "Разрешены только JPG, PNG, "
                        "WEBP, GIF, MP4, WEBM "
                        "и MOV."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_size = getattr(
            media,
            "size",
            0,
        )

        if file_size <= 0:
            return Response(
                {
                    "detail": (
                        "Файл истории пустой."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file_size > MAX_STORY_FILE_SIZE:
            return Response(
                {
                    "detail": (
                        "Максимальный размер файла "
                        "— 50 МБ."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_decorations = request.data.get(
            "decorations",
            [],
        )

        try:
            decorations = parse_decorations(
                raw_decorations,
            )
        except ValueError as error:
            return Response(
                {
                    "detail": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allow_reactions = request.data.get(
            "allow_reactions",
            True,
        )

        if isinstance(
            allow_reactions,
            str,
        ):
            allow_reactions = (
                allow_reactions.lower()
                in {
                    "true",
                    "1",
                    "yes",
                    "on",
                }
            )
        else:
            allow_reactions = bool(
                allow_reactions,
            )

        expires_at = (
            timezone.now()
            + timedelta(hours=24)
        )

        with transaction.atomic():
            story = Story.objects.create(
                author=request.user,
                media=media,
                media_type=media_type,
                text=text,
                decorations=decorations,
                allow_reactions=allow_reactions,
                expires_at=expires_at,
            )

        story = (
            stories_queryset()
            .get(id=story.id)
        )

        serializer = StorySerializer(
            story,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class StoryViewCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, story_id):
        story = get_active_story(story_id)

        if story is None:
            return story_not_found_response()

        if not user_can_access_story(
            request.user,
            story,
        ):
            return story_not_found_response()

        StoryView.objects.update_or_create(
            story=story,
            user=request.user,
            defaults={
                "viewed_at": timezone.now(),
            },
        )

        return Response(
            {
                "detail": "История просмотрена.",
            },
            status=status.HTTP_200_OK,
        )


class StoryDeleteView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, story_id):
        story = (
            Story.objects
            .filter(
                id=story_id,
                author=request.user,
            )
            .first()
        )

        if story is None:
            return Response(
                {
                    "detail": (
                        "История не найдена "
                        "или нет прав."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        story.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class StoryReactionView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, story_id):
        story = get_active_story(story_id)

        if story is None:
            return story_not_found_response()

        if not user_can_access_story(
            request.user,
            story,
        ):
            return story_not_found_response()

        if not story.allow_reactions:
            return Response(
                {
                    "detail": (
                        "Реакции для этой истории "
                        "отключены."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        reaction = request.data.get(
            "reaction",
        )

        allowed_reactions = {
            reaction_value
            for reaction_value, _ in (
                StoryReaction.REACTION_CHOICES
            )
        }

        if reaction not in allowed_reactions:
            return Response(
                {
                    "detail": (
                        "Недопустимая реакция."
                    ),
                    "allowed": [
                        value
                        for value, _ in (
                            StoryReaction.REACTION_CHOICES
                        )
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        StoryReaction.objects.update_or_create(
            story=story,
            user=request.user,
            defaults={
                "reaction": reaction,
            },
        )

        reactions_count = (
            StoryReaction.objects
            .filter(
                story=story,
            )
            .count()
        )

        return Response(
            {
                "reaction": reaction,
                "reactions_count": reactions_count,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, story_id):
        story = get_active_story(story_id)

        if story is None:
            return story_not_found_response()

        if not user_can_access_story(
            request.user,
            story,
        ):
            return story_not_found_response()

        deleted_count, _ = (
            StoryReaction.objects
            .filter(
                story=story,
                user=request.user,
            )
            .delete()
        )

        if deleted_count == 0:
            return Response(
                {
                    "detail": (
                        "Реакция не найдена."
                    ),
                    "reaction": None,
                    "reactions_count": (
                        StoryReaction.objects
                        .filter(story=story)
                        .count()
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        reactions_count = (
            StoryReaction.objects
            .filter(
                story=story,
            )
            .count()
        )

        return Response(
            {
                "reaction": None,
                "reactions_count": reactions_count,
            },
            status=status.HTTP_200_OK,
        )