from django.urls import path

from .views import CreatePostView
from .views import DeleteCommentView
from .views import DeletePostView
from .views import FeedView
from .views import FollowersView
from .views import FollowingView
from .views import FollowUserView
from .views import LikePostView
from .views import MyPostsView
from .views import PinPostView
from .views import PostCommentsView
from .views import SavedPostsView
from .views import SavePostView
from .views import UnfollowUserView
from .views import UnlikePostView
from .views import UserPostsView
from .views import ReelsFeedView
from .views import AcceptFollowRequestView
from .views import FollowRequestsView
from .views import RejectFollowRequestView

urlpatterns = [
    path(
        "create/",
        CreatePostView.as_view(),
        name="create-post",
    ),

    path(
        "feed/",
        FeedView.as_view(),
        name="feed",
    ),

    path(
    "reels/",
    ReelsFeedView.as_view(),
    name="reels-feed",
),

    path(
        "my/",
        MyPostsView.as_view(),
        name="my-posts",
    ),

    path(
        "saved/",
        SavedPostsView.as_view(),
        name="saved-posts",
    ),

    path(
        "users/<uuid:user_id>/posts/",
        UserPostsView.as_view(),
        name="user-posts",
    ),

    path(
        "users/<uuid:user_id>/follow/",
        FollowUserView.as_view(),
        name="follow-user",
    ),

    path(
        "users/<uuid:user_id>/unfollow/",
        UnfollowUserView.as_view(),
        name="unfollow-user",
    ),

    path(
        "followers/",
        FollowersView.as_view(),
        name="followers",
    ),

    path(
        "following/",
        FollowingView.as_view(),
        name="following",
    ),

    path(
        "<uuid:post_id>/save/",
        SavePostView.as_view(),
        name="save-post",
    ),

    path(
        "<uuid:post_id>/pin/",
        PinPostView.as_view(),
        name="pin-post",
    ),

    path(
        "<uuid:post_id>/delete/",
        DeletePostView.as_view(),
        name="delete-post",
    ),

    path(
        "<uuid:post_id>/like/",
        LikePostView.as_view(),
        name="like-post",
    ),

    path(
        "<uuid:post_id>/unlike/",
        UnlikePostView.as_view(),
        name="unlike-post",
    ),

    path(
        "<uuid:post_id>/comments/",
        PostCommentsView.as_view(),
        name="post-comments",
    ),

    path(
        "comments/<uuid:comment_id>/delete/",
        DeleteCommentView.as_view(),
        name="delete-comment",
    ),
        path(
        "follow-requests/",
        FollowRequestsView.as_view(),
        name="follow-requests",
    ),

    path(
        "follow-requests/<uuid:follow_id>/accept/",
        AcceptFollowRequestView.as_view(),
        name="accept-follow-request",
    ),

    path(
        "follow-requests/<uuid:follow_id>/reject/",
        RejectFollowRequestView.as_view(),
        name="reject-follow-request",
    ),
]