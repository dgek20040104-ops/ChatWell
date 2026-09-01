import os
import hashlib
import json
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import urlopen
from rest_framework.parsers import FormParser
from rest_framework.parsers import JSONParser
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Q
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from apps.posts.models import Follow

from .models import User
from .models import VerificationCode
from .serializers import PublicUserSerializer
from .serializers import RequestCodeSerializer
from .serializers import UserSerializer
from .serializers import VerifyCodeSerializer


CODE_LIFETIME_MINUTES = 5
MAX_CODE_ATTEMPTS = 5
RESEND_TIMEOUT_SECONDS = 60


def hash_code(code):
    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()


def generate_code():
    dev_code = os.environ.get(
        "DEV_SMS_CODE",
        "",
    ).strip()

    if dev_code:
        return dev_code

    return f"{secrets.randbelow(1_000_000):06d}"

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def send_sms_code(
    phone,
    code,
):
    mode = getattr(
        settings,
        "SMS_MODE",
        "console",
    )

    mode = str(
        mode
    ).strip().lower()

    if mode == "console":
        print(
            "[ChatWell] DEV SMS: "
            f"phone={phone} code={code}",
            flush=True,
        )

        return True

    if mode != "smsru":
        raise RuntimeError(
            "Неизвестный SMS_MODE. "
            "Используйте console или smsru."
        )

    api_id = getattr(
        settings,
        "SMS_RU_API_ID",
        "",
    )

    api_id = str(
        api_id
    ).strip()

    if not api_id:
        raise RuntimeError(
            "В Render не указан SMS_RU_API_ID."
        )

    message = (
        "ChatWell. Ваш код подтверждения: "
        f"{code}"
    )

    params = urlencode(
        {
            "api_id": api_id,
            "to": phone,
            "msg": message,
            "json": 1,
        }
    )

    url = (
        "https://sms.ru/sms/send?"
        + params
    )

    try:
        with urlopen(
            url,
            timeout=15,
        ) as response:
            response_text = (
                response.read()
                .decode(
                    "utf-8"
                )
            )
    except Exception as error:
        raise RuntimeError(
            "Не удалось подключиться к SMS.RU."
        ) from error

    try:
        response_data = json.loads(
            response_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "SMS.RU вернул некорректный ответ."
        ) from error

    print(
        "[ChatWell] SMS.RU response: "
        f"{response_data}",
        flush=True,
    )

    if response_data.get("status") != "OK":
        raise RuntimeError(
            str(
                response_data.get(
                    "status_text",
                    "SMS.RU отклонил отправку.",
                )
            )
        )

    sms_result = (
        response_data
        .get(
            "sms",
            {},
        )
        .get(
            phone,
            {},
        )
    )

    if sms_result.get("status") != "OK":
        raise RuntimeError(
            str(
                sms_result.get(
                    "status_text",
                    "SMS не было отправлено.",
                )
            )
        )

    return True


class RequestVerificationCodeView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        serializer = RequestCodeSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        phone = serializer.validated_data[
            "phone"
        ]

        cache_key = (
            f"verification-resend:{phone}"
        )

        if cache.get(cache_key):
            return Response(
                {
                    "detail": (
                        "Повторно запросить код можно "
                        "через "
                        f"{RESEND_TIMEOUT_SECONDS} секунд."
                    ),
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        is_existing_user = (
            User.objects
            .filter(
                phone=phone,
                is_active=True,
            )
            .exists()
        )

        code = generate_code()

        VerificationCode.objects.filter(
            phone=phone,
            is_used=False,
        ).update(
            is_used=True,
        )

        verification = (
            VerificationCode.objects.create(
                phone=phone,
                code_hash=hash_code(code),
                expires_at=(
                    timezone.now()
                    + timedelta(
                        minutes=CODE_LIFETIME_MINUTES,
                    )
                ),
            )
        )

        try:
            send_sms_code(
                phone,
                code,
            )
        except Exception as error:
            verification.is_used = True

            verification.save(
                update_fields=[
                    "is_used",
                ],
            )

            print(
                f"[ChatWell] SMS sending error: {error}"
            )

            return Response(
                {
                    "detail": (
                        "Не удалось отправить код. "
                        "Попробуйте ещё раз."
                    ),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        cache.set(
            cache_key,
            True,
            timeout=RESEND_TIMEOUT_SECONDS,
        )

        response_data = {
            "detail": (
                "Код подтверждения отправлен."
            ),
            "expires_in": (
                CODE_LIFETIME_MINUTES * 60
            ),
            "is_existing_user": (
                is_existing_user
            ),
        }

        if settings.DEBUG:
            response_data["debug_code"] = code

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


class VerifyVerificationCodeView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        serializer = VerifyCodeSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        phone = serializer.validated_data[
            "phone"
        ]

        code = serializer.validated_data[
            "code"
        ]

        username = (
            serializer.validated_data.get(
                "username",
                "",
            )
            or ""
        ).strip()

        display_name = (
            serializer.validated_data.get(
                "display_name",
                "",
            )
            or ""
        ).strip()

        verification = (
            VerificationCode.objects
            .filter(
                phone=phone,
                is_used=False,
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        if verification is None:
            return Response(
                {
                    "detail": (
                        "Код не найден или уже "
                        "использован."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.is_expired():
            return Response(
                {
                    "detail": (
                        "Срок действия кода истёк."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.attempts >= (
            MAX_CODE_ATTEMPTS
        ):
            return Response(
                {
                    "detail": (
                        "Превышено количество попыток."
                    ),
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if verification.code_hash != hash_code(code):
            verification.attempts += 1

            verification.save(
                update_fields=[
                    "attempts",
                ],
            )

            attempts_left = (
                MAX_CODE_ATTEMPTS
                - verification.attempts
            )

            return Response(
                {
                    "detail": "Неверный код.",
                    "attempts_left": max(
                        attempts_left,
                        0,
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = (
            User.objects
            .filter(
                phone=phone,
            )
            .first()
        )

        is_new_user = user is None

        if is_new_user and not username:
            return Response(
                {
                    "username": [
                        (
                            "Для нового пользователя "
                            "необходимо указать тег."
                        )
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_new_user and not display_name:
            return Response(
                {
                    "display_name": [
                        (
                            "Для нового пользователя "
                            "необходимо указать имя."
                        )
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_new_user:
            username_exists = (
                User.objects
                .filter(
                    username__iexact=username,
                )
                .exists()
            )

            if username_exists:
                return Response(
                    {
                        "username": [
                            (
                                "Пользователь с таким "
                                "тегом уже существует."
                            )
                        ],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        verification.is_used = True

        verification.save(
            update_fields=[
                "is_used",
            ],
        )

        if is_new_user:
            user = User.objects.create_user(
                phone=phone,
                username=username,
                display_name=display_name,
                is_phone_verified=True,
                is_active=True,
            )
        else:
            update_fields = []

            if not user.is_phone_verified:
                user.is_phone_verified = True

                update_fields.append(
                    "is_phone_verified",
                )

            # Для существующего пользователя
            # username и имя не требуются.
            # Существующие данные не изменяются
            # во время обычного входа.

            if update_fields:
                user.save(
                    update_fields=update_fields,
                )

        tokens = get_tokens_for_user(user)

        user_data = UserSerializer(
            user,
            context={
                "request": request,
            },
        ).data

        return Response(
            {
                "user": user_data,
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "is_new_user": is_new_user,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get(self, request):
        return Response(
            UserSerializer(
                request.user,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UserSearchView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        query = request.query_params.get(
            "q",
            "",
        ).strip().lstrip("@")

        if len(query) < 2:
            return Response(
                [],
                status=status.HTTP_200_OK,
            )

        following_subquery = (
            Follow.objects.filter(
                follower=request.user,
                following=OuterRef("pk"),
                is_accepted=True,
            )
        )

        pending_subquery = (
            Follow.objects.filter(
                follower=request.user,
                following=OuterRef("pk"),
                is_accepted=False,
            )
        )

        users = (
            User.objects
            .filter(
                is_active=True,
            )
            .exclude(
                id=request.user.id,
            )
            .filter(
                Q(username__icontains=query)
                | Q(display_name__icontains=query)
            )
            .annotate(
                followers_count=Count(
                    "follower_relations",
                    filter=Q(
                        follower_relations__is_accepted=True,
                    ),
                    distinct=True,
                ),
                following_count=Count(
                    "following_relations",
                    filter=Q(
                        following_relations__is_accepted=True,
                    ),
                    distinct=True,
                ),
                is_following=Exists(
                    following_subquery,
                ),
                is_pending=Exists(
                    pending_subquery,
                ),
            )
            .order_by(
                "username",
                "display_name",
            )[:20]
        )

        return Response(
            PublicUserSerializer(
                users,
                many=True,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )


class PublicUserProfileView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, user_id):
        following_subquery = (
            Follow.objects.filter(
                follower=request.user,
                following=OuterRef("pk"),
                is_accepted=True,
            )
        )

        pending_subquery = (
            Follow.objects.filter(
                follower=request.user,
                following=OuterRef("pk"),
                is_accepted=False,
            )
        )

        try:
            user = (
                User.objects
                .filter(
                    id=user_id,
                    is_active=True,
                )
                .annotate(
                    followers_count=Count(
                        "follower_relations",
                        filter=Q(
                            follower_relations__is_accepted=True,
                        ),
                        distinct=True,
                    ),
                    following_count=Count(
                        "following_relations",
                        filter=Q(
                            following_relations__is_accepted=True,
                        ),
                        distinct=True,
                    ),
                    is_following=Exists(
                        following_subquery,
                    ),
                    is_pending=Exists(
                        pending_subquery,
                    ),
                )
                .get()
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

        return Response(
            PublicUserSerializer(
                user,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )

