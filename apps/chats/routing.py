from django.urls import re_path

from .consumers import ChatConsumer
from .notifications_consumer import NotificationsConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/notifications/$",
        NotificationsConsumer.as_asgi(),
    ),

    re_path(
        r"^ws/chats/(?P<chat_id>[0-9a-f-]+)/$",
        ChatConsumer.as_asgi(),
    ),
]