from django.urls import path

from .views import ReelsPageView


urlpatterns = [
    path(
        "",
        ReelsPageView.as_view(),
        name="reels-page",
    ),
]