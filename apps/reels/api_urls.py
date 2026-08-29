from django.urls import path

from .views import ReelsFeedView


urlpatterns = [
    path(
        "",
        ReelsFeedView.as_view(),
        name="reels-feed",
    ),
]