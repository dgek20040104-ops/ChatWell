import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 1. Сначала запускаем Django (загружаем приложения)
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# 2. Только теперь импортируем компоненты Channels
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# 3. Импортируем твои роуты и middleware ТОЛЬКО ПОСЛЕ setup()
# Если здесь вылетит ошибка - значит проблема точно в коде внутри этих файлов
from apps.chats.routing import websocket_urlpatterns
from apps.chats.middleware import JWTAuthMiddleware

# ВАЖНО: Правильный порядок обертки
# Вариант А: Если JWTAuthMiddleware должен работать ВМЕСТО стандартной авторизации для WS
# Обычно JWT middleware сам должен оборачивать inner app.
# Но чаще всего делают так:

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
