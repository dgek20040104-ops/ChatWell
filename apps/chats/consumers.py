import json
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer,
)
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Chat
from .models import ChatMember
from .models import Message
from .serializers import MessageSerializer


class ChatConsumer(
    AsyncJsonWebsocketConsumer
):
    async def connect(self):
        self.chat_id = (
            self.scope
            .get("url_route", {})
            .get("kwargs", {})
            .get("chat_id")
        )

        self.user = self.scope.get("user")

        if (
            self.user is None
            or not self.user.is_authenticated
        ):
            await self.close(code=4401)
            return

        if not self.chat_id:
            await self.close(code=4403)
            return

        self.chat = await self.get_chat_access()

        if self.chat is None:
            await self.close(code=4403)
            return

        self.group_name = (
            f"chat_{self.chat.id}"
        )

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await self.set_user_online()

        membership = await self.get_membership()

        can_send_messages = (
            await self.check_can_send_messages(
                membership
            )
        )

        await self.send_json(
            {
                "type": "connection",
                "chat_id": str(
                    self.chat.id
                ),
                "user_id": str(
                    self.user.id
                ),
                "is_online": True,
                "can_send_messages": (
                    can_send_messages
                ),
            }
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence_event",
                "user_id": str(
                    self.user.id
                ),
                "username": getattr(
                    self.user,
                    "username",
                    "",
                ),
                "is_online": True,
                "last_seen": None,
            }
        )

    async def disconnect(
        self,
        close_code,
    ):
        if not hasattr(
            self,
            "group_name",
        ):
            return

        await self.set_user_offline()

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence_event",
                "user_id": str(
                    self.user.id
                ),
                "username": getattr(
                    self.user,
                    "username",
                    "",
                ),
                "is_online": False,
                "last_seen": timezone.now().isoformat(),
            }
        )

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def receive_json(
        self,
        content,
        **kwargs,
    ):
        if not isinstance(
            content,
            dict,
        ):
            await self.send_error(
                "Некорректный формат сообщения."
            )
            return

        message_type = content.get("type")

        if message_type == "message":
            await self.receive_message(content)
            return

        if message_type == "typing":
            await self.receive_typing(content)
            return

        if message_type == "read":
            await self.mark_as_read(content)
            return

        await self.send_error(
            "Неизвестный тип сообщения."
        )

    async def receive_message(
        self,
        content,
    ):
        text = content.get("text", "")

        if not isinstance(text, str):
            await self.send_error(
                "Текст сообщения должен быть строкой."
            )
            return

        text = text.strip()

        if not text:
            await self.send_error(
                "Сообщение не может быть пустым."
            )
            return

        if len(text) > 5000:
            await self.send_error(
                "Сообщение не может быть длиннее "
                "5000 символов."
            )
            return

        membership = await self.get_membership()

        if membership is None:
            await self.send_error(
                "Вы не состоите в этом чате."
            )
            return

        can_send = (
            await self.check_can_send_messages(
                membership
            )
        )

        if not can_send:
            await self.send_error(
                "В этом сообществе писать могут "
                "только администраторы."
            )
            return

        reply_to_id = content.get("reply_to")
        reply_to = None

        if reply_to_id:
            if not self.is_valid_uuid(
                reply_to_id
            ):
                await self.send_error(
                    "Некорректный ID сообщения."
                )
                return

            reply_to = (
                await self.get_reply_message(
                    reply_to_id
                )
            )

            if reply_to is None:
                await self.send_error(
                    "Сообщение для ответа не найдено."
                )
                return

            if reply_to.is_deleted:
                await self.send_error(
                    "Нельзя ответить на удалённое "
                    "сообщение."
                )
                return

        message = await self.create_message(
            text=text,
            reply_to=reply_to,
        )

        if message is None:
            await self.send_error(
                "Не удалось сохранить сообщение."
            )
            return

        serialized_message = (
            await self.serialize_message(
                message
            )
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": serialized_message,
            }
        )

        await self.broadcast_new_message_notifications(
            serialized_message
        )

    async def receive_typing(
        self,
        content,
    ):
        membership = await self.get_membership()

        if membership is None:
            return

        is_typing = content.get(
            "is_typing",
            False,
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_event",
                "user_id": str(
                    self.user.id
                ),
                "username": getattr(
                    self.user,
                    "username",
                    "",
                ),
                "is_typing": bool(is_typing),
            }
        )

    async def mark_as_read(
        self,
        content,
    ):
        message_id = content.get("message_id")

        if message_id:
            if not self.is_valid_uuid(
                message_id
            ):
                await self.send_error(
                    "Некорректный ID сообщения."
                )
                return

            message = (
                await self.get_message_for_read(
                    message_id
                )
            )

            if message is not None:
                await self.mark_message_as_read(
                    message
                )

                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "message_read",
                        "message_id": str(
                            message.id
                        ),
                        "user_id": str(
                            self.user.id
                        ),
                    }
                )

        membership = await self.get_membership()

        if membership is not None:
            await self.update_last_read(
                membership
            )

    async def broadcast_new_message_notifications(
        self,
        message_data,
    ):
        member_ids = (
            await self.get_other_member_ids()
        )

        for user_id in member_ids:
            await self.channel_layer.group_send(
                f"user_notifications_{user_id}",
                {
                    "type": "notification_message",
                    "chat_id": str(
                        self.chat.id
                    ),
                    "message": message_data,
                },
            )

    async def send_error(
        self,
        detail,
    ):
        await self.send_json(
            {
                "type": "error",
                "detail": detail,
            }
        )

    async def chat_message(
        self,
        event,
    ):
        message = self.make_json_safe(
            event.get("message", {})
        )

        await self.send_json(
            {
                "type": "message",
                "message": message,
            }
        )

    async def message_updated(
        self,
        event,
    ):
        message = self.make_json_safe(
            event.get("message", {})
        )

        await self.send_json(
            {
                "type": "message_updated",
                "message": message,
            }
        )

    async def message_deleted(
        self,
        event,
    ):
        message = self.make_json_safe(
            event.get("message", {})
        )

        await self.send_json(
            {
                "type": "message_deleted",
                "message": message,
            }
        )

    async def message_read(
        self,
        event,
    ):
        await self.send_json(
            {
                "type": "message_read",
                "message_id": str(
                    event.get(
                        "message_id",
                        "",
                    )
                ),
                "user_id": str(
                    event.get(
                        "user_id",
                        "",
                    )
                ),
            }
        )

    async def presence_event(
        self,
        event,
    ):
        if (
            str(self.user.id)
            == str(event.get("user_id"))
        ):
            return

        await self.send_json(
            {
                "type": "presence",
                "user_id": str(
                    event.get(
                        "user_id",
                        "",
                    )
                ),
                "username": event.get(
                    "username",
                    "",
                ),
                "is_online": bool(
                    event.get(
                        "is_online",
                        False,
                    )
                ),
                "last_seen": event.get(
                    "last_seen"
                ),
            }
        )

    async def typing_event(
        self,
        event,
    ):
        if (
            str(self.user.id)
            == str(event.get("user_id"))
        ):
            return

        await self.send_json(
            {
                "type": "typing",
                "user_id": str(
                    event.get(
                        "user_id",
                        "",
                    )
                ),
                "username": event.get(
                    "username",
                    "",
                ),
                "is_typing": bool(
                    event.get(
                        "is_typing",
                        False,
                    )
                ),
            }
        )

    @staticmethod
    def is_valid_uuid(value):
        try:
            uuid.UUID(str(value))
            return True
        except (
            ValueError,
            AttributeError,
            TypeError,
        ):
            return False

    @staticmethod
    def make_json_safe(data):
        return json.loads(
            json.dumps(
                data,
                default=str,
            )
        )

    @database_sync_to_async
    def get_chat_access(self):
        return (
            Chat.objects
            .filter(
                id=self.chat_id,
                members__user=self.user,
            )
            .first()
        )

    @database_sync_to_async
    def get_membership(self):
        if self.chat is None:
            return None

        return (
            ChatMember.objects
            .filter(
                chat=self.chat,
                user=self.user,
            )
            .first()
        )

    @database_sync_to_async
    def get_other_member_ids(self):
        return list(
            ChatMember.objects
            .filter(chat=self.chat)
            .exclude(user=self.user)
            .values_list(
                "user_id",
                flat=True,
            )
        )

    @database_sync_to_async
    def check_can_send_messages(
        self,
        membership,
    ):
        if membership is None:
            return False

        if self.chat.chat_type != Chat.CHANNEL:
            return True

        return membership.role in {
            ChatMember.OWNER,
            ChatMember.ADMIN,
        }

    @database_sync_to_async
    def get_reply_message(
        self,
        reply_to_id,
    ):
        try:
            return (
                Message.objects
                .filter(
                    id=reply_to_id,
                    chat=self.chat,
                )
                .select_related(
                    "sender",
                    "reply_to",
                )
                .first()
            )
        except (
            ValidationError,
            ValueError,
        ):
            return None

    @database_sync_to_async
    def create_message(
        self,
        text,
        reply_to=None,
    ):
        message = Message.objects.create(
            chat=self.chat,
            sender=self.user,
            message_type=Message.TEXT,
            text=text,
            reply_to=reply_to,
        )

        Chat.objects.filter(
            id=self.chat.id,
        ).update(
            updated_at=message.created_at,
        )

        return (
            Message.objects
            .filter(id=message.id)
            .select_related(
                "chat",
                "sender",
                "reply_to",
            )
            .first()
        )

    @database_sync_to_async
    def get_message_for_read(
        self,
        message_id,
    ):
        try:
            return (
                Message.objects
                .filter(
                    id=message_id,
                    chat=self.chat,
                )
                .first()
            )
        except (
            ValidationError,
            ValueError,
        ):
            return None

    @database_sync_to_async
    def mark_message_as_read(
        self,
        message,
    ):
        message.read_by.add(self.user)

        if message.sender_id != self.user.id:
            message.is_delivered = True
            message.delivered_at = timezone.now()

            message.save(
                update_fields=[
                    "is_delivered",
                    "delivered_at",
                ]
            )

    @database_sync_to_async
    def serialize_message(
        self,
        message,
    ):
        data = MessageSerializer(
            message,
            context={
                "request": None,
            },
        ).data

        return self.make_json_safe(data)

    @database_sync_to_async
    def update_last_read(
        self,
        membership,
    ):
        membership.last_read_at = timezone.now()

        membership.save(
            update_fields=[
                "last_read_at",
            ]
        )

    @database_sync_to_async
    def set_user_online(self):
        self.user.is_online = True
        self.user.last_seen = timezone.now()

        self.user.save(
            update_fields=[
                "is_online",
                "last_seen",
            ]
        )

    @database_sync_to_async
    def set_user_offline(self):
        self.user.is_online = False
        self.user.last_seen = timezone.now()

        self.user.save(
            update_fields=[
                "is_online",
                "last_seen",
            ]
        )