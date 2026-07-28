from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.welcome, name="welcome"),
    path("chats/", views.dashboard, name="dashboard"),
    path("search/", views.search, name="search"),
    path("groups/create/", views.create_group, name="create_group"),
    path(
        "start/<str:username>/",
        views.start_private_chat,
        name="start_private_chat",
    ),
    path("chat/<int:conversation_id>/", views.room, name="room"),
    path(
        "chat/<int:conversation_id>/send/",
        views.send_attachment,
        name="send_attachment",
    ),
    path("messages/<int:message_id>/edit/", views.edit_message, name="edit_message"),
    path("messages/<int:message_id>/delete/", views.delete_message, name="delete_message"),
    path("messages/<int:message_id>/react/", views.react_to_message, name="react_message"),
    path("messages/<int:message_id>/pin/", views.toggle_pin_message, name="pin_message"),
    path("messages/<int:message_id>/forward/", views.forward_message, name="forward_message"),
    path("messages/<int:message_id>/info/", views.message_info, name="message_info"),
    path("chat/<int:conversation_id>/action/", views.conversation_action, name="conversation_action"),
    path(
        "groups/<int:conversation_id>/",
        views.group_room,
        name="group_room",
    ),
    path(
        "groups/<int:conversation_id>/settings/",
        views.group_settings,
        name="group_settings",
    ),
    path(
        "groups/<int:conversation_id>/leave/",
        views.leave_group,
        name="leave_group",
    ),
    path(
        "groups/<int:conversation_id>/delete/",
        views.delete_group,
        name="delete_group",
    ),
    path("groups/join/<str:invite_code>/", views.join_group, name="join_group"),
    path("groups/<int:conversation_id>/invite/regenerate/", views.regenerate_invite, name="regenerate_invite"),
]
