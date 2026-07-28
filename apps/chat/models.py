from django.conf import settings
from django.db import models
import secrets

class Conversation(models.Model):
    name = models.CharField(max_length=120, blank=True)
    is_group = models.BooleanField(default=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="group_icons/", blank=True, null=True)
    invite_code = models.CharField(max_length=40, unique=True, blank=True, null=True)
    members_can_send = models.BooleanField(default=True)
    members_can_edit_info = models.BooleanField(default=False)

    def ensure_invite_code(self):
        if not self.invite_code:
            self.invite_code = secrets.token_urlsafe(18)
            self.save(update_fields=["invite_code"])
        return self.invite_code

    @classmethod
    def private_between(cls, first_user, second_user):
        return (
            cls.objects.filter(is_group=False, participants=first_user)
            .filter(participants=second_user)
            .distinct()
            .first()
        )

    def other_participant(self, current_user):
        return self.participants.exclude(pk=current_user.pk).first()

    def __str__(self):
        return self.name or f"Conversation {self.pk}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replies",
        blank=True,
        null=True,
    )
    content = models.TextField(max_length=4000, blank=True)
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    document = models.FileField(upload_to="documents/", blank=True, null=True)
    voice_note = models.FileField(upload_to="voice_notes/", blank=True, null=True)
    is_read = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    forwarded_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, related_name="forwards",
        blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    hidden_for = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="hidden_chat_messages"
    )
    pinned_at = models.DateTimeField(blank=True, null=True)
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pinned_chat_messages",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:40]}"

class MessageReaction(models.Model):
    ALLOWED_EMOJIS = ("👍", "❤️", "😂", "😮", "😢", "🙏")

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_reactions",
    )
    emoji = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("message", "user", "emoji"),
                name="unique_message_user_emoji",
            ),
        ]

    def __str__(self):
        return f"{self.user}: {self.emoji}"


class ConversationPreference(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="preferences"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="conversation_preferences",
    )
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    marked_unread = models.BooleanField(default=False)
    cleared_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("conversation", "user"),
                name="unique_conversation_user_preference",
            )
        ]


class MessageReceipt(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="receipts"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="message_receipts",
    )
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("message", "user"), name="unique_message_recipient_receipt"
            )
        ]
