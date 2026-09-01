import os


from channels.routing import (
    ProtocolTypeRouter,
    URLRouter,
)


from django.core.asgi import (
    get_asgi_application,
)


from apps.chats.middleware import (
    JWTAuthMiddlewareStack,
)


from apps.chats.routing import (
    websocket_urlpatterns,
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


django_asgi_application = (
    get_asgi_application()
)


application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,

        "websocket": JWTAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        ),
    }
)
