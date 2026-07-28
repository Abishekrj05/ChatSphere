from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils.html import strip_tags
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from apps.notifications.services import notify_message
from .models import Conversation, MessageReceipt
from .services import create_message, messaging_error, serialize_message
from .utils import user_display_name

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = int(
            self.scope["url_route"]["kwargs"]["conversation_id"]
        )
        self.group_name = f"chat_{self.conversation_id}"

        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self.has_access():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()
        await self.set_online(True)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence.event", "user_id": self.user.pk,
                "username": await self.get_display_name(), "is_online": True,
            },
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )
        if getattr(self, "user", None) and self.user.is_authenticated:
            still_online = await self.set_online(False)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.event", "user_id": self.user.pk,
                    "username": await self.get_display_name(), "is_online": still_online,
                },
            )

    async def receive_json(self, content, **kwargs):
        event_type = content.get("type")

        if event_type == "typing":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "typing.event",
                    "user_id": self.user.pk,
                    "username": await self.get_display_name(),
                    "is_typing": bool(content.get("is_typing")),
                },
            )
            return

        if event_type != "message":
            return

        text = strip_tags(str(content.get("message", ""))).strip()
        if not text:
            return

        reply_to_id = content.get("reply_to")
        try:
            saved_message = await self.save_message(text[:4000], reply_to_id)
        except PermissionError as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": saved_message,
            },
        )
    async def chat_message(self, event):
        if event["message"]["sender_id"] != self.user.pk:
            receipt = await self.mark_delivered(event["message"]["id"])
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.event", "event": receipt},
            )
        await self.send_json({"type": "message", **event["message"]})

    async def chat_event(self, event):
        await self.send_json({"type": "message_event", **event["event"]})

    async def typing_event(self, event):
        if event["user_id"] != self.user.pk:
            await self.send_json(
                {
                    "type": "typing",
                    "username": event["username"],
                    "is_typing": event["is_typing"],
                }
            )

    async def presence_event(self, event):
        if event["user_id"] != self.user.pk:
            await self.send_json({"type": "presence", **event})

    @database_sync_to_async
    def has_access(self):
        return Conversation.objects.filter(
            pk=self.conversation_id,
            participants=self.user,
        ).exists()

    @database_sync_to_async
    def save_message(self, text, reply_to_id=None):
        conversation = Conversation.objects.get(pk=self.conversation_id)
        error = messaging_error(conversation, self.user)
        if error:
            raise PermissionError(error)
        reply_to = None
        if reply_to_id:
            reply_to = conversation.messages.filter(pk=reply_to_id).first()
        message = create_message(
            conversation,
            self.user,
            text,
            reply_to=reply_to,
        )
        notify_message(message)
        return serialize_message(message)

    @database_sync_to_async
    def set_online(self, value):
        from apps.accounts.models import Profile
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(user=self.user)
            if value:
                profile.active_connections = F("active_connections") + 1
                profile.is_online = True
                profile.save(update_fields=["active_connections", "is_online"])
                return True
            else:
                profile.active_connections = max(0, profile.active_connections - 1)
                profile.is_online = profile.active_connections > 0
                profile.last_seen = timezone.now()
                profile.save(update_fields=["active_connections", "is_online", "last_seen"])
                return profile.is_online

    @database_sync_to_async
    def get_display_name(self):
        return user_display_name(self.user)

    @database_sync_to_async
    def mark_delivered(self, message_id):
        message = Conversation.objects.get(pk=self.conversation_id).messages.get(pk=message_id)
        receipt, _ = MessageReceipt.objects.get_or_create(
            message=message, user=self.user
        )
        if not receipt.delivered_at:
            receipt.delivered_at = timezone.now()
            receipt.save(update_fields=["delivered_at"])
        all_receipts = message.receipts.all()
        all_delivered = (
            all_receipts.exists()
            and not all_receipts.filter(delivered_at__isnull=True).exists()
        )
        if all_delivered and not message.delivered_at:
            message.delivered_at = timezone.now()
            message.save(update_fields=["delivered_at"])
        return {
            "action": "status", "message_id": message.pk,
            "status": "delivered" if all_delivered else "sent",
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else "",
        }
