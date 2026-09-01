from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Chat
from .models import ChatMember
from .models import Message

from .serializers import AddMemberSerializer
from .serializers import ChatMemberSerializer
from .serializers import ChatSerializer
from .serializers import CreateChannelSerializer
from .serializers import CreateFileMessageSerializer
from .serializers import CreateGroupSerializer
from .serializers import CreateMessageSerializer
from .serializers import CreatePrivateChatSerializer
from .serializers import MessageSerializer
from .serializers import UserSearchSerializer


User = get_user_model()


def get_chat_for_user(chat_id, user):
    return (
        Chat.objects
        .filter(
            id=chat_id,
            members__user=user,
        )
        .first()
    )


def get_membership(chat, user):
    return (
        ChatMember.objects
        .filter(
            chat=chat,
            user=user,
        )
        .first()
    )


def is_manager(membership):
    return (
        membership is not None
        and membership.role in {
            ChatMember.OWNER,
            ChatMember.ADMIN,
        }
    )


def serialize_chat(chat, request):
    return ChatSerializer(
        chat,
        context={
            "request": request,
        },
    ).data


def broadcast_message(chat, message_data):
    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(
        f"chat_{chat.id}",
        {
            "type": "chat_message",
            "message": message_data,
        },
    )


def broadcast_new_message_notifications(
    chat,
    message_data,
    sender_id,
):
    channel_layer = get_channel_layer()

    member_ids = (
        ChatMember.objects
        .filter(
            chat=chat,
        )
        .exclude(
            user_id=sender_id,
        )
        .values_list(
            "user_id",
            flat=True,
        )
    )

    for user_id in member_ids:
        async_to_sync(
            channel_layer.group_send
        )(
            f"user_notifications_{user_id}",
            {
                "type": "notification_message",
                "chat_id": str(chat.id),
                "message": message_data,
            },
        )


def broadcast_message_updated(chat, message_data):
    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(
        f"chat_{chat.id}",
        {
            "type": "message_updated",
            "message": message_data,
        },
    )


def broadcast_message_deleted(chat, message_data):
    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(
        f"chat_{chat.id}",
        {
            "type": "message_deleted",
            "message": message_data,
        },
    )


class UserSearchView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        query = (
            request.query_params
            .get("q", "")
            .strip()
            .lstrip("@")
        )

        if len(query) < 2:
            return Response(
                [],
                status=status.HTTP_200_OK,
            )

        users = (
            User.objects
            .filter(
                Q(username__icontains=query)
                | Q(display_name__icontains=query),
                is_active=True,
            )
            .exclude(
                id=request.user.id,
            )
            .order_by(
                "username",
            )[:20]
        )

        serializer = UserSearchSerializer(
            users,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ChatListCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        chats = (
            Chat.objects
            .filter(
                members__user=request.user,
            )
            .prefetch_related(
                "members__user",
                "messages__sender",
            )
            .distinct()
            .order_by(
                "-updated_at",
            )
        )

        serializer = ChatSerializer(
            chats,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = CreatePrivateChatSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        username = serializer.validated_data[
            "username"
        ]

        target_user = (
            User.objects
            .filter(
                username__iexact=username,
                is_active=True,
            )
            .first()
        )

        if target_user is None:
            return Response(
                {
                    "detail": "Пользователь не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        existing_chat = (
            Chat.objects
            .filter(
                chat_type=Chat.PRIVATE,
                members__user=request.user,
            )
            .filter(
                members__user=target_user,
            )
            .distinct()
            .first()
        )

        if existing_chat is not None:
            return Response(
                serialize_chat(
                    existing_chat,
                    request,
                ),
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            chat = Chat.objects.create(
                chat_type=Chat.PRIVATE,
                owner=request.user,
            )

            ChatMember.objects.bulk_create(
                [
                    ChatMember(
                        chat=chat,
                        user=request.user,
                        role=ChatMember.OWNER,
                    ),
                    ChatMember(
                        chat=chat,
                        user=target_user,
                        role=ChatMember.MEMBER,
                    ),
                ]
            )

        return Response(
            serialize_chat(
                chat,
                request,
            ),
            status=status.HTTP_201_CREATED,
        )


class CreateGroupView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = CreateGroupSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        usernames = serializer.validated_data.get(
            "usernames",
            [],
        )

        users = []

        for username in usernames:
            user = (
                User.objects
                .filter(
                    username__iexact=username,
                    is_active=True,
                )
                .exclude(
                    id=request.user.id,
                )
                .first()
            )

            if user is not None and user not in users:
                users.append(user)

        with transaction.atomic():
            chat = Chat.objects.create(
                chat_type=Chat.GROUP,
                title=serializer.validated_data[
                    "title"
                ],
                description=serializer.validated_data.get(
                    "description",
                    "",
                ),
                owner=request.user,
                is_public=False,
            )

            members = [
                ChatMember(
                    chat=chat,
                    user=request.user,
                    role=ChatMember.OWNER,
                )
            ]

            members.extend(
                ChatMember(
                    chat=chat,
                    user=user,
                    role=ChatMember.MEMBER,
                )
                for user in users
            )

            ChatMember.objects.bulk_create(
                members,
            )

        return Response(
            serialize_chat(
                chat,
                request,
            ),
            status=status.HTTP_201_CREATED,
        )


class CreateChannelView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = CreateChannelSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        with transaction.atomic():
            chat = Chat.objects.create(
                chat_type=Chat.CHANNEL,
                title=serializer.validated_data[
                    "title"
                ],
                description=serializer.validated_data.get(
                    "description",
                    "",
                ),
                is_public=serializer.validated_data.get(
                    "is_public",
                    True,
                ),
                owner=request.user,
            )

            ChatMember.objects.create(
                chat=chat,
                user=request.user,
                role=ChatMember.OWNER,
            )

        return Response(
            serialize_chat(
                chat,
                request,
            ),
            status=status.HTTP_201_CREATED,
        )


class ChatMessagesView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_chat(self, request, chat_id):
        return get_chat_for_user(
            chat_id,
            request.user,
        )

    def get(self, request, chat_id):
        chat = self.get_chat(
            request,
            chat_id,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = (
            Message.objects
            .filter(
                chat=chat,
            )
            .select_related(
                "chat",
                "sender",
                "reply_to",
            )
            .order_by(
                "created_at",
            )
        )

        ChatMember.objects.filter(
            chat=chat,
            user=request.user,
        ).update(
            last_read_at=timezone.now(),
        )

        serializer = MessageSerializer(
            messages,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, chat_id):
        chat = self.get_chat(
            request,
            chat_id,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            chat,
            request.user,
        )

        if (
            chat.chat_type == Chat.CHANNEL
            and not is_manager(membership)
        ):
            return Response(
                {
                    "detail": (
                        "В этом сообществе писать "
                        "могут только администраторы."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateMessageSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        reply_to_id = serializer.validated_data.get(
            "reply_to",
        )

        reply_to = None

        if reply_to_id is not None:
            reply_to = (
                Message.objects
                .filter(
                    id=reply_to_id,
                    chat=chat,
                )
                .first()
            )

            if reply_to is None:
                return Response(
                    {
                        "detail": (
                            "Сообщение для ответа "
                            "не найдено."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if reply_to.is_deleted:
                return Response(
                    {
                        "detail": (
                            "Нельзя ответить на "
                            "удалённое сообщение."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            message = Message.objects.create(
                chat=chat,
                sender=request.user,
                message_type=Message.TEXT,
                text=serializer.validated_data[
                    "text"
                ],
                reply_to=reply_to,
            )

            Chat.objects.filter(
                id=chat.id,
            ).update(
                updated_at=timezone.now(),
            )

        message = (
            Message.objects
            .select_related(
                "chat",
                "sender",
                "reply_to",
            )
            .get(
                id=message.id,
            )
        )

        serialized_message = MessageSerializer(
            message,
            context={
                "request": request,
            },
        ).data

        broadcast_message(
            chat,
            serialized_message,
        )

        broadcast_new_message_notifications(
            chat,
            serialized_message,
            request.user.id,
        )

        return Response(
            serialized_message,
            status=status.HTTP_201_CREATED,
        )


class UploadMessageView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request, chat_id):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            chat,
            request.user,
        )

        if membership is None:
            return Response(
                {
                    "detail": "Вы не состоите в этом чате.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            chat.chat_type == Chat.CHANNEL
            and not is_manager(membership)
        ):
            return Response(
                {
                    "detail": (
                        "В этом сообществе писать "
                        "могут только администраторы."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateFileMessageSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        uploaded_file = serializer.validated_data[
            "file"
        ]

        text = serializer.validated_data.get(
            "text",
            "",
        )

        reply_to_id = serializer.validated_data.get(
            "reply_to",
        )

        reply_to = None

        if reply_to_id is not None:
            reply_to = (
                Message.objects
                .filter(
                    id=reply_to_id,
                    chat=chat,
                )
                .first()
            )

            if reply_to is None:
                return Response(
                    {
                        "detail": (
                            "Сообщение для ответа "
                            "не найдено."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if reply_to.is_deleted:
                return Response(
                    {
                        "detail": (
                            "Нельзя ответить на "
                            "удалённое сообщение."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        content_type = (
            uploaded_file.content_type or ""
        ).lower()

        if content_type.startswith("image/"):
            message_type = Message.IMAGE

        elif content_type.startswith("video/"):
            message_type = Message.VIDEO

        else:
            message_type = Message.FILE

        with transaction.atomic():
            message = Message.objects.create(
                chat=chat,
                sender=request.user,
                message_type=message_type,
                text=text,
                file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=content_type,
                reply_to=reply_to,
            )

            Chat.objects.filter(
                id=chat.id,
            ).update(
                updated_at=timezone.now(),
            )

        message = (
            Message.objects
            .select_related(
                "chat",
                "sender",
                "reply_to",
            )
            .get(
                id=message.id,
            )
        )

        serialized_message = MessageSerializer(
            message,
            context={
                "request": request,
            },
        ).data

        broadcast_message(
            chat,
            serialized_message,
        )

        broadcast_new_message_notifications(
            chat,
            serialized_message,
            request.user.id,
        )

        return Response(
            serialized_message,
            status=status.HTTP_201_CREATED,
        )


class ChatMembersView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, chat_id):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        members = (
            ChatMember.objects
            .filter(
                chat=chat,
            )
            .select_related(
                "user",
            )
            .order_by(
                "role",
                "joined_at",
            )
        )

        serializer = ChatMemberSerializer(
            members,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class AddChatMemberView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, chat_id):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            chat,
            request.user,
        )

        if not is_manager(membership):
            return Response(
                {
                    "detail": "Недостаточно прав.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if chat.chat_type == Chat.PRIVATE:
            return Response(
                {
                    "detail": (
                        "В личный чат нельзя "
                        "добавлять участников."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AddMemberSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.user_object

        member, created = (
            ChatMember.objects.get_or_create(
                chat=chat,
                user=user,
                defaults={
                    "role": ChatMember.MEMBER,
                },
            )
        )

        if not created:
            return Response(
                {
                    "detail": (
                        "Пользователь уже состоит "
                        "в этом чате."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ChatMemberSerializer(
                member,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
        )


class RemoveChatMemberView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, chat_id, user_id):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        current_membership = get_membership(
            chat,
            request.user,
        )

        if not is_manager(current_membership):
            return Response(
                {
                    "detail": "Недостаточно прав.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        target_membership = (
            ChatMember.objects
            .filter(
                chat=chat,
                user_id=user_id,
            )
            .first()
        )

        if target_membership is None:
            return Response(
                {
                    "detail": "Участник не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_membership.role == ChatMember.OWNER:
            return Response(
                {
                    "detail": "Владельца нельзя удалить.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            target_membership.role == ChatMember.ADMIN
            and current_membership.role
            != ChatMember.OWNER
        ):
            return Response(
                {
                    "detail": (
                        "Только владелец может "
                        "удалять администратора."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        target_membership.delete()

        return Response(
            {
                "detail": "Участник удалён.",
            },
            status=status.HTTP_200_OK,
        )


class LeaveChatView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, chat_id):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            chat,
            request.user,
        )

        if membership is None:
            return Response(
                {
                    "detail": "Вы не состоите в чате.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role == ChatMember.OWNER:
            return Response(
                {
                    "detail": (
                        "Владелец не может выйти "
                        "из чата. Передайте права "
                        "другому участнику или удалите чат."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()

        return Response(
            {
                "detail": "Вы вышли из чата.",
            },
            status=status.HTTP_200_OK,
        )


class EditMessageView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def patch(self, request, chat_id, message_id):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        message = (
            Message.objects
            .filter(
                id=message_id,
                chat=chat,
            )
            .select_related(
                "chat",
                "sender",
                "reply_to",
            )
            .first()
        )

        if message is None:
            return Response(
                {
                    "detail": "Сообщение не найдено.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if message.sender_id != request.user.id:
            return Response(
                {
                    "detail": (
                        "Можно редактировать "
                        "только свои сообщения."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if message.is_deleted:
            return Response(
                {
                    "detail": (
                        "Удалённое сообщение "
                        "нельзя редактировать."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        text = request.data.get(
            "text",
            "",
        )

        if not isinstance(text, str):
            return Response(
                {
                    "detail": (
                        "Текст сообщения должен "
                        "быть строкой."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        text = text.strip()

        if not text:
            return Response(
                {
                    "detail": (
                        "Сообщение не может "
                        "быть пустым."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(text) > 5000:
            return Response(
                {
                    "detail": (
                        "Сообщение не может быть "
                        "длиннее 5000 символов."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        message.text = text
        message.is_edited = True

        message.save(
            update_fields=[
                "text",
                "is_edited",
                "updated_at",
            ]
        )

        serialized_message = MessageSerializer(
            message,
            context={
                "request": request,
            },
        ).data

        broadcast_message_updated(
            chat,
            serialized_message,
        )

        return Response(
            serialized_message,
            status=status.HTTP_200_OK,
        )


class DeleteMessageView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(
        self,
        request,
        chat_id,
        message_id,
    ):
        chat = get_chat_for_user(
            chat_id,
            request.user,
        )

        if chat is None:
            return Response(
                {
                    "detail": "Чат не найден.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        message = (
            Message.objects
            .filter(
                id=message_id,
                chat=chat,
            )
            .select_related(
                "chat",
                "sender",
                "reply_to",
            )
            .first()
        )

        if message is None:
            return Response(
                {
                    "detail": "Сообщение не найдено.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            chat,
            request.user,
        )

        can_delete = (
            message.sender_id
            == request.user.id
            or is_manager(
                membership,
            )
        )

        if not can_delete:
            return Response(
                {
                    "detail": (
                        "У вас нет права удалять "
                        "это сообщение."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if message.is_deleted:
            return Response(
                {
                    "detail": (
                        "Сообщение уже удалено."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        message.is_deleted = True
        message.text = ""
        message.file = None
        message.file_name = ""
        message.file_size = None
        message.mime_type = ""

        message.save(
            update_fields=[
                "is_deleted",
                "text",
                "file",
                "file_name",
                "file_size",
                "mime_type",
                "updated_at",
            ],
        )

        serialized_message = (
            MessageSerializer(
                message,
                context={
                    "request": request,
                },
            ).data
        )

        broadcast_message_deleted(
            chat,
            serialized_message,
        )

        return Response(
            serialized_message,
            status=status.HTTP_200_OK,
        )
