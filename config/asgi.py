import os


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


from django.core.asgi import get_asgi_application


django_asgi_application = (
    get_asgi_application()
)


from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter


from apps.chats.jwt_middleware import (
    JWTAuthMiddlewareStack,
)
from apps.chats.routing import (
    websocket_urlpatterns,
)


application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,

        "websocket": JWTAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns,
            ),
        ),
    },
)
