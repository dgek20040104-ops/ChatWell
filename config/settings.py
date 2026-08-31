import os

from datetime import timedelta
from pathlib import Path

import dj_database_url
import environ

from dotenv import load_dotenv


# ==================================================
# Базовые настройки
# ==================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


load_dotenv(
    BASE_DIR / ".env"
)


env = environ.Env(
    DEBUG=(
        bool,
        False,
    ),
)


environ.Env.read_env(
    BASE_DIR / ".env"
)


# ==================================================
# Вспомогательные функции
# ==================================================

def get_env_list(
    name,
    default="",
):
    value = os.environ.get(
        name,
        default,
    )

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ==================================================
# Основные настройки
# ==================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    env(
        "DJANGO_SECRET_KEY",
        default=(
            "unsafe-development-secret-key"
        ),
    ),
)


DEBUG = (
    os.environ.get(
        "DEBUG",
        "False",
    )
    .strip()
    .lower()
    in {
        "true",
        "1",
        "yes",
        "on",
    }
)


# ==================================================
# Hosts и CSRF
# ==================================================

ALLOWED_HOSTS = get_env_list(
    "ALLOWED_HOSTS",
    default=(
        "localhost,"
        "127.0.0.1,"
        "0.0.0.0,"
        "chatwell-9we6.onrender.com"
    ),
)


CSRF_TRUSTED_ORIGINS = get_env_list(
    "CSRF_TRUSTED_ORIGINS",
    default=(
        "http://localhost:8000,"
        "http://127.0.0.1:8000,"
        "https://chatwell-9we6.onrender.com"
    ),
)


# ==================================================
# Приложения
# ==================================================

INSTALLED_APPS = [
    "daphne",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    "storages",

    "apps.accounts.apps.AccountsConfig",
    "apps.core.apps.CoreConfig",
    "apps.posts.apps.PostsConfig",
    "apps.chats.apps.ChatsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.stories.apps.StoriesConfig",
    "apps.reels.apps.ReelsConfig",
]


# ==================================================
# Middleware
# ==================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==================================================
# URL и шаблоны
# ==================================================

ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django."
            "DjangoTemplates"
        ),

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                (
                    "django.template.context_processors."
                    "request"
                ),
                (
                    "django.contrib.auth.context_processors."
                    "auth"
                ),
                (
                    "django.contrib.messages.context_processors."
                    "messages"
                ),
            ],
        },
    },
]


# ==================================================
# WSGI / ASGI
# ==================================================

WSGI_APPLICATION = (
    "config.wsgi.application"
)


ASGI_APPLICATION = (
    "config.asgi.application"
)


# ==================================================
# База данных
# ==================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()


if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        ),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": (
                "django.db.backends.sqlite3"
            ),
            "NAME": (
                BASE_DIR / "db.sqlite3"
            ),
        },
    }


# ==================================================
# Пользовательская модель
# ==================================================

AUTH_USER_MODEL = "accounts.User"


# ==================================================
# Пароли
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
]


PASSWORD_HASHERS = [
    (
        "django.contrib.auth.hashers."
        "Argon2PasswordHasher"
    ),
    (
        "django.contrib.auth.hashers."
        "PBKDF2PasswordHasher"
    ),
]


# ==================================================
# Язык и время
# ==================================================

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ==================================================
# Статические файлы
# ==================================================

STATIC_URL = "/static/"

STATIC_ROOT = (
    BASE_DIR / "staticfiles"
)


STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ==================================================
# Пользовательские файлы
# ==================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = (
    BASE_DIR / "media"
)


FILE_UPLOAD_MAX_MEMORY_SIZE = (
    25 * 1024 * 1024
)


DATA_UPLOAD_MAX_MEMORY_SIZE = (
    110 * 1024 * 1024
)


# ==================================================
# Yandex Object Storage
# ==================================================

AWS_ACCESS_KEY_ID = os.environ.get(
    "AWS_ACCESS_KEY_ID",
    "",
).strip()


AWS_SECRET_ACCESS_KEY = os.environ.get(
    "AWS_SECRET_ACCESS_KEY",
    "",
).strip()


AWS_STORAGE_BUCKET_NAME = os.environ.get(
    "AWS_STORAGE_BUCKET_NAME",
    "",
).strip()


AWS_S3_ENDPOINT_URL = (
    "https://storage.yandexcloud.net"
)


AWS_S3_REGION_NAME = (
    "ru-central1"
)


AWS_S3_SIGNATURE_VERSION = (
    "s3v4"
)


AWS_DEFAULT_ACL = None

AWS_S3_FILE_OVERWRITE = False

AWS_QUERYSTRING_AUTH = True

AWS_QUERYSTRING_EXPIRE = 3600

AWS_S3_VERIFY = True


AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": (
        "max-age=86400"
    ),
}


STORAGES = {
    "default": {
        "BACKEND": (
            "storages.backends.s3.S3Storage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ==================================================
# Первичный ключ
# ==================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ==================================================
# CORS
# ==================================================

CORS_ALLOWED_ORIGINS = get_env_list(
    "CORS_ALLOWED_ORIGINS",
    default=(
        "http://localhost:8000,"
        "http://127.0.0.1:8000,"
        "https://chatwell-9we6.onrender.com"
    ),
)


CORS_ALLOW_CREDENTIALS = True


# ==================================================
# Django REST Framework
# ==================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication."
        "JWTAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}


# ==================================================
# JWT
# ==================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=15,
    ),

    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=30,
    ),

    "ROTATE_REFRESH_TOKENS": True,

    "BLACKLIST_AFTER_ROTATION": True,

    "UPDATE_LAST_LOGIN": True,

    "ALGORITHM": "HS256",

    "AUTH_HEADER_TYPES": (
        "Bearer",
    ),
}


# ==================================================
# SMS.RU
# ==================================================

SMS_RU_API_ID = env(
    "SMS_RU_API_ID",
    default="",
).strip()


# ==================================================
# Безопасность
# ==================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = (
    "same-origin"
)

X_FRAME_OPTIONS = "DENY"


SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


if DEBUG:
    SECURE_SSL_REDIRECT = False

    SESSION_COOKIE_SECURE = False

    CSRF_COOKIE_SECURE = False

    SECURE_HSTS_SECONDS = 0

    SECURE_HSTS_INCLUDE_SUBDOMAINS = False

    SECURE_HSTS_PRELOAD = False
else:
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 31536000

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True


# ==================================================
# Channels и Redis
# ==================================================

REDIS_URL = os.environ.get(
    "REDIS_URL",
    "",
).strip()


USE_REDIS = (
    os.environ.get(
        "USE_REDIS",
        "false",
    )
    .strip()
    .lower()
    in {
        "true",
        "1",
        "yes",
        "on",
    }
)


if USE_REDIS and REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": (
                "channels_redis.core."
                "RedisChannelLayer"
            ),

            "CONFIG": {
                "hosts": [
                    REDIS_URL,
                ],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": (
                "channels.layers."
                "InMemoryChannelLayer"
            ),
        },
    }
