from django.urls import path

from .views import ReelsFeedView
from .views import ReelsPageView


urlpatterns = [
    path(
        "",
        ReelsFeedView.as_view(),
        name="reels-feed",
    ),

    path(
        "page/",
        ReelsPageView.as_view(),
        name="reels-page",
    ),
]