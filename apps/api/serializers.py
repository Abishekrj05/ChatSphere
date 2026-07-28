from rest_framework import serializers
from apps.chat.models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.profile.name", read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "content",
            "image",
            "document",
            "voice_note",
            "is_read",
            "created_at",
        )
        read_only_fields = (
            "id",
            "conversation",
            "sender",
            "is_read",
            "created_at",
        )

    def validate(self, attrs):
        if not any(
            attrs.get(field)
            for field in ("content", "image", "document", "voice_note")
        ):
            raise serializers.ValidationError(
                "Enter a message or attach a file."
            )
        return attrs

class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "name",
            "is_group",
            "participants",
            "created_at",
            "updated_at",
            "messages",
        )
