from django.urls import path

from .views import chat
from .views import feed
from .views import people
from .views import profile
from .views import public_user_profile
from .views import register
from .views import notifications
from .views import settings_page
urlpatterns = [
    path(
        "",
        feed,
        name="home",
    ),

    path(
        "home/",
        feed,
        name="home-page",
    ),

    path(
        "feed/",
        feed,
        name="feed",
    ),

    path(
        "register/",
        register,
        name="register",
    ),

    path(
        "profile/",
        profile,
        name="profile",
    ),

    path(
        "people/",
        people,
        name="people",
    ),

    path(
        "chat/",
        chat,
        name="chat",
    ),

    path(
        "users/<uuid:user_id>/",
        public_user_profile,
        name="public-user-profile",
    ),

    path(
    "notifications/",
    notifications,
    name="notifications",
),

path(
    "settings/",
    settings_page,
    name="settings",
),
]