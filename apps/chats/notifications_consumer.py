from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer,
)


class NotificationsConsumer(
    AsyncJsonWebsocketConsumer
):
    async def connect(self):
        self.user = self.scope.get("user")

        if (
            self.user is None
            or not self.user.is_authenticated
        ):
            await self.close(
                code=4401
            )
            return

        self.group_name = (
            f"user_notifications_{self.user.id}"
        )

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send_json(
            {
                "type": "notifications_connection",
                "user_id": str(
                    self.user.id
                ),
            }
        )

    async def disconnect(
        self,
        close_code
    ):
        if not hasattr(
            self,
            "group_name"
        ):
            return

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def receive_json(
        self,
        content,
        **kwargs
    ):
        # В этом соединении клиент ничего
        # отправлять не обязан.
        return

    async def notification_message(
        self,
        event
    ):
        await self.send_json(
            {
                "type": "new_message",
                "chat_id": str(
                    event.get(
                        "chat_id",
                        "",
                    )
                ),
                "message": event.get(
                    "message",
                    {},
                ),
            }
        )