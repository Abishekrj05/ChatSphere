from django.urls import path
from .views import ConversationListAPIView, MessageListCreateAPIView

app_name = "api"

urlpatterns = [
    path("conversations/", ConversationListAPIView.as_view(), name="conversations"),
    path(
        "conversations/<int:conversation_id>/messages/",
        MessageListCreateAPIView.as_view(),
        name="messages",
    ),
]
