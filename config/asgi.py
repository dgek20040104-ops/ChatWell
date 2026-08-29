import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

from django.core.asgi import get_asgi_application

# Здесь происходит загрузка приложений — django.setup()
django_asgi_app = get_asgi_application()

# Все импорты, которые тянут Django-модели, — ТОЛЬКО ПОСЛЕ setup()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter

from apps.chats.middleware import JWTAuthMiddleware
from apps.chats.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
