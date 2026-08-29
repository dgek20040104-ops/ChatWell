from django.urls import path

from .views import StoryCreateView
from .views import StoryDeleteView
from .views import StoryListView
from .views import StoryReactionView
from .views import StoryViewCreateView


urlpatterns = [
    path(
        "",
        StoryListView.as_view(),
        name="story-list",
    ),

    path(
        "create/",
        StoryCreateView.as_view(),
        name="story-create",
    ),

    path(
        "<uuid:story_id>/view/",
        StoryViewCreateView.as_view(),
        name="story-view",
    ),

    path(
        "<uuid:story_id>/react/",
        StoryReactionView.as_view(),
        name="story-react",
    ),

    path(
        "<uuid:story_id>/delete/",
        StoryDeleteView.as_view(),
        name="story-delete",
    ),
]