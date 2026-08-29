from django.urls import path

from .views import AddChatMemberView
from .views import ChatListCreateView
from .views import ChatMembersView
from .views import ChatMessagesView
from .views import CreateChannelView
from .views import CreateGroupView
from .views import DeleteMessageView
from .views import EditMessageView
from .views import LeaveChatView
from .views import RemoveChatMemberView
from .views import UploadMessageView
from .views import UserSearchView


urlpatterns = [
    path(
        "",
        ChatListCreateView.as_view(),
        name="chat-list-create",
    ),

    path(
        "users/search/",
        UserSearchView.as_view(),
        name="chat-user-search",
    ),

    path(
        "groups/create/",
        CreateGroupView.as_view(),
        name="group-create",
    ),

    path(
        "channels/create/",
        CreateChannelView.as_view(),
        name="channel-create",
    ),

    path(
        "<uuid:chat_id>/messages/upload/",
        UploadMessageView.as_view(),
        name="message-upload",
    ),

    path(
        "<uuid:chat_id>/messages/<uuid:message_id>/edit/",
        EditMessageView.as_view(),
        name="message-edit",
    ),

    path(
        "<uuid:chat_id>/messages/<uuid:message_id>/delete/",
        DeleteMessageView.as_view(),
        name="message-delete",
    ),

    path(
        "<uuid:chat_id>/messages/",
        ChatMessagesView.as_view(),
        name="chat-messages",
    ),

    path(
        "<uuid:chat_id>/members/",
        ChatMembersView.as_view(),
        name="chat-members",
    ),

    path(
        "<uuid:chat_id>/members/add/",
        AddChatMemberView.as_view(),
        name="chat-member-add",
    ),

    path(
        "<uuid:chat_id>/members/<uuid:user_id>/remove/",
        RemoveChatMemberView.as_view(),
        name="chat-member-remove",
    ),

    path(
        "<uuid:chat_id>/leave/",
        LeaveChatView.as_view(),
        name="chat-leave",
    ),
]