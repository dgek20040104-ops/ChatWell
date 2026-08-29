from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path(
        "",
        include("apps.core.urls"),
    ),

    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/auth/",
        include("apps.accounts.urls"),
    ),

    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),

    path(
        "api/posts/",
        include("apps.posts.urls"),
    ),

    path(
        "api/chats/",
        include("apps.chats.urls"),
    ),

    path(
        "api/notifications/",
        include("apps.notifications.urls"),
    ),

    path(
        "api/stories/",
        include("apps.stories.urls"),
    ),

    path(
        "api/reels/",
        include("apps.reels.api_urls"),
    ),

    path(
        "reels/",
        include("apps.reels.page_urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )