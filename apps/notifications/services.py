from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification
from apps.chat.utils import user_display_name
from apps.chat.models import ConversationPreference


def notify_message(message):
    """Persist and broadcast a notification to every recipient."""
    sender = message.sender
    conversation = message.conversation
    preview = message.content or "Sent an attachment"
    title = (
        f"New message in {conversation.name}"
        if conversation.is_group
        else f"New message from {user_display_name(sender)}"
    )
    channel_layer = get_channel_layer()

    for recipient in conversation.participants.exclude(pk=sender.pk):
        if ConversationPreference.objects.filter(
            conversation=conversation, user=recipient, is_muted=True
        ).exists():
            continue
        if not conversation.is_group and (
            recipient.profile.blocked_users.filter(pk=sender.pk).exists()
            or sender.profile.blocked_users.filter(pk=recipient.pk).exists()
        ):
            continue
        notification = Notification.objects.create(
            recipient=recipient,
            conversation=conversation,
            title=title,
            message=preview[:300],
        )
        async_to_sync(channel_layer.group_send)(
            f"notifications_{recipient.pk}",
            {
                "type": "notification.message",
                "notification": {
                    "id": notification.pk,
                    "title": notification.title,
                    "message": notification.message,
                    "conversation_id": conversation.pk,
                },
            },
        )
