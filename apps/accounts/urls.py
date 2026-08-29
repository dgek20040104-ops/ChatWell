from django.urls import path

from .views import MeView
from .views import RequestVerificationCodeView
from .views import VerifyVerificationCodeView
from .views import UserSearchView
from .views import PublicUserProfileView
urlpatterns = [
    path(
        "request-code/",
        RequestVerificationCodeView.as_view(),
        name="request-code",
    ),
    path(
        "verify-code/",
        VerifyVerificationCodeView.as_view(),
        name="verify-code",
    ),
    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
    path(
    "users/search/",
    UserSearchView.as_view(),
    name="user-search",
),
path(
    "users/<uuid:user_id>/",
    PublicUserProfileView.as_view(),
    name="public-user-profile",
),
]