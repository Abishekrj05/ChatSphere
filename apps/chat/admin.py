from django.contrib import admin
from .models import Conversation, ConversationPreference, Message, MessageReaction, MessageReceipt

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "content", "created_at")

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_group",
        "created_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_group", "created_at")
    filter_horizontal = ("participants",)
    inlines = (MessageInline,)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = ("content", "sender__username")

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "emoji", "created_at")
    list_filter = ("emoji", "created_at")

@admin.register(ConversationPreference)
class ConversationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("conversation", "user", "is_pinned", "is_muted", "is_archived")
    list_filter = ("is_pinned", "is_muted", "is_archived")

@admin.register(MessageReceipt)
class MessageReceiptAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "delivered_at", "read_at")
    list_filter = ("delivered_at", "read_at")
