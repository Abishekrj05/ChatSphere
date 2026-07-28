from django.db import models
from django.utils import timezone
from .models import Conversation, Message, MessageReceipt
from .utils import user_display_name


def messaging_error(conversation, sender):
    if conversation.is_group:
        if not conversation.members_can_send and conversation.created_by_id != sender.pk:
            return "Only the group owner can send messages."
        return ""
    other = conversation.other_participant(sender)
    if other and (
        sender.profile.blocked_users.filter(pk=other.pk).exists()
        or other.profile.blocked_users.filter(pk=sender.pk).exists()
    ):
        return "Messaging is unavailable for this conversation."
    return ""

def get_or_create_private_conversation(first_user, second_user):
    conversation = Conversation.private_between(first_user, second_user)
    if conversation:
        return conversation

    conversation = Conversation.objects.create(
        is_group=False,
        created_by=first_user,
    )
    conversation.participants.add(first_user, second_user)
    return conversation

def create_message(conversation, sender, content="", **files):
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=content,
        reply_to=files.get("reply_to"),
        forwarded_from=files.get("forwarded_from"),
        image=files.get("image"),
        document=files.get("document"),
        voice_note=files.get("voice_note"),
    )
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])
    MessageReceipt.objects.bulk_create([
        MessageReceipt(message=message, user_id=user_id)
        for user_id in conversation.participants.exclude(
            pk=sender.pk
        ).values_list("pk", flat=True)
    ])
    return message


def mark_messages_read(conversation, user):
    now = timezone.now()
    receipts = MessageReceipt.objects.filter(
        message__conversation=conversation, user=user, read_at__isnull=True
    )
    message_ids = list(receipts.values_list("message_id", flat=True))
    receipts.update(delivered_at=now, read_at=now)
    events = []
    for message in Message.objects.filter(pk__in=message_ids):
        all_receipts = message.receipts.all()
        if all_receipts.exists() and not all_receipts.filter(read_at__isnull=True).exists():
            message.is_read = True
            message.read_at = now
            if not message.delivered_at:
                message.delivered_at = now
            message.save(update_fields=["is_read", "read_at", "delivered_at"])
            events.append({
                "action": "status", "message_id": message.pk,
                "status": "read", "read_at": now.isoformat(),
            })
    return events

def serialize_message(message):
    def file_url(field):
        return field.url if field else ""

    return {
        "id": message.pk,
        "sender_id": message.sender_id,
        "sender": user_display_name(message.sender),
        "content": "" if message.is_deleted else message.content,
        "is_deleted": message.is_deleted,
        "edited_at": message.edited_at.isoformat() if message.edited_at else "",
        "is_pinned": bool(message.pinned_at),
        "is_forwarded": bool(message.forwarded_from_id),
        "delivered_at": message.delivered_at.isoformat() if message.delivered_at else "",
        "read_at": message.read_at.isoformat() if message.read_at else "",
        "status": "read" if message.read_at or message.is_read else ("delivered" if message.delivered_at else "sent"),
        "reply_to": (
            {
                "id": message.reply_to_id,
                "sender": user_display_name(message.reply_to.sender),
                "content": message.reply_to.content[:120],
            }
            if message.reply_to_id else None
        ),
        "image_url": file_url(message.image),
        "document_url": file_url(message.document),
        "document_name": message.document.name.rsplit("/", 1)[-1] if message.document else "",
        "voice_note_url": file_url(message.voice_note),
        "created_at": message.created_at.isoformat(),
        "reactions": [
            {"emoji": item["emoji"], "count": item["count"]}
            for item in message.reactions.values("emoji")
            .annotate(count=models.Count("id"))
            .order_by("emoji")
        ],
    }
