from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from apps.notifications.models import Notification
from .models import Conversation, ConversationPreference, Message, MessageReaction, MessageReceipt
from .services import create_message, get_or_create_private_conversation, mark_messages_read
from apps.notifications.services import notify_message

class ChatTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("user1", password="StrongPass123")
        self.user2 = User.objects.create_user("user2", password="StrongPass123")

    def test_private_conversation_is_reused(self):
        first = get_or_create_private_conversation(self.user1, self.user2)
        second = get_or_create_private_conversation(self.user1, self.user2)
        self.assertEqual(first.pk, second.pk)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("chat:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_welcome_page_loads_for_guest(self):
        response = self.client.get(reverse("chat:welcome"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conversations that feel effortless.")

    def test_welcome_redirects_authenticated_user(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse("chat:welcome"))
        self.assertRedirects(response, reverse("chat:dashboard"))

    def test_non_participant_cannot_open_room(self):
        outsider = User.objects.create_user("outsider", password="StrongPass123")
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        self.client.force_login(outsider)
        response = self.client.get(reverse("chat:room", args=[conversation.pk]))
        self.assertEqual(response.status_code, 404)

    def test_group_creation_adds_creator_and_members(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("chat:create_group"),
            {"name": "Project team", "participants": [self.user2.pk]},
        )
        conversation = Conversation.objects.get(name="Project team")
        self.assertRedirects(
            response,
            reverse("chat:group_room", args=[conversation.pk]),
        )
        self.assertEqual(
            set(conversation.participants.values_list("pk", flat=True)),
            {self.user1.pk, self.user2.pk},
        )

    def test_attachment_endpoint_persists_and_notifies(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        self.client.force_login(self.user1)
        document = SimpleUploadedFile("notes.txt", b"project notes")
        response = self.client.post(
            reverse("chat:send_attachment", args=[conversation.pk]),
            {"content": "Please review", "document": document},
        )
        self.assertEqual(response.status_code, 201)
        message = Message.objects.get(conversation=conversation)
        self.assertEqual(message.content, "Please review")
        self.assertTrue(message.document.name.endswith("notes.txt"))
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user2,
                conversation=conversation,
            ).exists()
        )
        message.document.delete(save=False)

    def test_opening_room_marks_messages_and_notifications_read(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user2, "Unread")
        notify_message(message)
        self.client.force_login(self.user1)
        self.client.get(reverse("chat:room", args=[conversation.pk]))
        message.refresh_from_db()
        notification = Notification.objects.get(recipient=self.user1)
        self.assertTrue(message.is_read)
        self.assertTrue(notification.is_read)

    def test_api_message_creation_updates_and_notifies(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("api:messages", args=[conversation.pk]),
            {"content": "API message"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user2,
                message="API message",
            ).exists()
        )

    def test_api_rejects_non_participant(self):
        outsider = User.objects.create_user("outsider", password="StrongPass123")
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        self.client.force_login(outsider)
        response = self.client.get(
            reverse("api:messages", args=[conversation.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_sender_can_edit_message(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user1, "Before")
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("chat:edit_message", args=[message.pk]),
            data='{"content": "After"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertEqual(message.content, "After")
        self.assertIsNotNone(message.edited_at)

    def test_non_sender_cannot_edit_message(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user1, "Private")
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("chat:edit_message", args=[message.pk]),
            data='{"content": "Changed"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_sender_can_soft_delete_message(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user1, "Remove me")
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("chat:delete_message", args=[message.pk])
        )
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertTrue(message.is_deleted)
        self.assertEqual(message.content, "")

    def test_participant_can_delete_message_only_for_self(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user1, "hide this")
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("chat:delete_message", args=[message.pk]),
            data='{"scope":"me"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message.hidden_for.filter(pk=self.user2.pk).exists())
        message.refresh_from_db()
        self.assertFalse(message.is_deleted)
        self.client.force_login(self.user1)
        self.assertContains(
            self.client.get(reverse("chat:room", args=[conversation.pk])),
            "hide this",
        )
    def test_participant_can_toggle_reaction(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user1, "React")
        self.client.force_login(self.user2)
        url = reverse("chat:react_message", args=[message.pk])
        first = self.client.post(url, {"emoji": "👍"})
        self.assertEqual(first.status_code, 200)
        self.assertTrue(
            MessageReaction.objects.filter(
                message=message, user=self.user2, emoji="👍"
            ).exists()
        )
        second = self.client.post(url, {"emoji": "👍"})
        self.assertEqual(second.status_code, 200)
        self.assertFalse(
            MessageReaction.objects.filter(message=message, user=self.user2).exists()
        )

    def test_search_only_returns_accessible_messages(self):
        own = get_or_create_private_conversation(self.user1, self.user2)
        create_message(own, self.user2, "visible keyword")
        outsider = User.objects.create_user("outsider", password="StrongPass123")
        hidden = get_or_create_private_conversation(self.user2, outsider)
        create_message(hidden, outsider, "hidden keyword")
        self.client.force_login(self.user1)
        response = self.client.get(reverse("chat:search"), {"q": "keyword"})
        self.assertContains(response, "visible keyword")
        self.assertNotContains(response, "hidden keyword")

    def test_group_owner_can_update_members(self):
        conversation = Conversation.objects.create(
            name="Old name",
            is_group=True,
            created_by=self.user1,
        )
        conversation.participants.add(self.user1, self.user2)
        third = User.objects.create_user("third", password="StrongPass123")
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("chat:group_settings", args=[conversation.pk]),
            {"name": "New name", "participants": [third.pk]},
        )
        self.assertRedirects(
            response,
            reverse("chat:group_room", args=[conversation.pk]),
        )
        conversation.refresh_from_db()
        self.assertEqual(conversation.name, "New name")
        self.assertEqual(
            set(conversation.participants.values_list("pk", flat=True)),
            {self.user1.pk, third.pk},
        )

    def test_group_member_can_leave(self):
        conversation = Conversation.objects.create(
            name="Team",
            is_group=True,
            created_by=self.user1,
        )
        conversation.participants.add(self.user1, self.user2)
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("chat:leave_group", args=[conversation.pk])
        )
        self.assertRedirects(response, reverse("chat:dashboard"))
        self.assertFalse(conversation.participants.filter(pk=self.user2.pk).exists())

    def test_user_can_pin_and_mute_a_conversation(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        self.client.force_login(self.user1)
        url = reverse("chat:conversation_action", args=[conversation.pk])
        self.assertEqual(self.client.post(url, {"action": "pin"}).status_code, 200)
        self.assertEqual(self.client.post(url, {"action": "mute"}).status_code, 200)
        preference = self.user1.conversation_preferences.get(conversation=conversation)
        self.assertTrue(preference.is_pinned)
        self.assertTrue(preference.is_muted)

    def test_sender_can_forward_message(self):
        source_conversation = get_or_create_private_conversation(self.user1, self.user2)
        third = User.objects.create_user("forward-target", password="StrongPass123")
        target = get_or_create_private_conversation(self.user1, third)
        source = create_message(source_conversation, self.user2, "forward me")
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("chat:forward_message", args=[source.pk]),
            {"conversation_id": target.pk},
        )
        self.assertEqual(response.status_code, 201)
        forwarded = target.messages.get()
        self.assertEqual(forwarded.content, "forward me")
        self.assertEqual(forwarded.forwarded_from_id, source.pk)

    def test_group_invite_adds_authenticated_member(self):
        group = Conversation.objects.create(
            name="Invited team", is_group=True, created_by=self.user1
        )
        group.participants.add(self.user1)
        code = group.ensure_invite_code()
        self.client.force_login(self.user2)
        response = self.client.get(reverse("chat:join_group", args=[code]))
        self.assertRedirects(response, reverse("chat:group_room", args=[group.pk]))
        self.assertTrue(group.participants.filter(pk=self.user2.pk).exists())

    def test_message_info_is_private_to_sender(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        message = create_message(conversation, self.user1, "status")
        self.client.force_login(self.user1)
        response = self.client.get(reverse("chat:message_info", args=[message.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "sent")

    def test_muted_conversation_does_not_create_notification(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        ConversationPreference.objects.create(
            conversation=conversation, user=self.user2, is_muted=True
        )
        message = create_message(conversation, self.user1, "quiet")
        notify_message(message)
        self.assertFalse(Notification.objects.filter(recipient=self.user2).exists())

    def test_blocked_user_cannot_send_attachment(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        self.user2.profile.blocked_users.add(self.user1)
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("chat:send_attachment", args=[conversation.pk]),
            {"content": "blocked message"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(conversation.messages.exists())

    def test_group_read_status_waits_for_every_recipient(self):
        third = User.objects.create_user("receipt-user", password="StrongPass123")
        conversation = Conversation.objects.create(
            name="Receipts", is_group=True, created_by=self.user1
        )
        conversation.participants.add(self.user1, self.user2, third)
        message = create_message(conversation, self.user1, "group status")
        self.assertEqual(message.receipts.count(), 2)
        mark_messages_read(conversation, self.user2)
        message.refresh_from_db()
        self.assertFalse(message.is_read)
        mark_messages_read(conversation, third)
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_archived_conversation_remains_available_for_restoring(self):
        conversation = get_or_create_private_conversation(self.user1, self.user2)
        ConversationPreference.objects.create(
            conversation=conversation, user=self.user1, is_archived=True
        )
        self.client.force_login(self.user1)
        response = self.client.get(reverse("chat:dashboard"))
        self.assertContains(response, 'data-conversation-archived="true"')
