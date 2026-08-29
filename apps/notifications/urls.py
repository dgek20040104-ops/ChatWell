from django.urls import path

from .views import NotificationListView
from .views import NotificationReadAllView
from .views import NotificationReadView


urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="notifications",
    ),

    path(
        "<uuid:notification_id>/read/",
        NotificationReadView.as_view(),
        name="notification-read",
    ),

    path(
        "read-all/",
        NotificationReadAllView.as_view(),
        name="notifications-read-all",
    ),
]