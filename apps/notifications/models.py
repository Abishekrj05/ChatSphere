from django.conf import settings
from django.db import models
from apps.chat.models import Conversation

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_notifications",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="notifications",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=300)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
