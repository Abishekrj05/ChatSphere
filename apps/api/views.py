from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.chat.models import Conversation
from apps.chat.services import create_message, messaging_error, serialize_message
from apps.notifications.services import notify_message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationListAPIView(generics.ListAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return (
            self.request.user.conversations
            .prefetch_related("participants", "messages__sender")
            .order_by("-updated_at")
        )

class MessageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer

    def get_conversation(self):
        conversation = Conversation.objects.filter(
            pk=self.kwargs["conversation_id"],
            participants=self.request.user,
        ).first()

        if conversation is None:
            raise PermissionDenied("You do not have access to this conversation.")

        return conversation

    def get_queryset(self):
        return self.get_conversation().messages.select_related("sender")

    def perform_create(self, serializer):
        validated = serializer.validated_data
        conversation = self.get_conversation()
        error = messaging_error(conversation, self.request.user)
        if error:
            raise PermissionDenied(error)
        message = create_message(
            conversation,
            self.request.user,
            validated.get("content", ""),
            image=validated.get("image"),
            document=validated.get("document"),
            voice_note=validated.get("voice_note"),
        )
        notify_message(message)
        async_to_sync(get_channel_layer().group_send)(
            f"chat_{conversation.pk}",
            {"type": "chat.message", "message": serialize_message(message)},
        )
        serializer.instance = message
