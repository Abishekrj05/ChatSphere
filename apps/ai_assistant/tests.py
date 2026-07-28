from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch


class AIAssistantTests(TestCase):
    def test_assistant_page_requires_authentication(self):
        response = self.client.get(reverse("ai_assistant:assistant"))
        self.assertEqual(response.status_code, 302)

    def test_assistant_page_has_suggestions_for_authenticated_user(self):
        user = User.objects.create_user("assistant-user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.get(reverse("ai_assistant:assistant"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How can I help today?")

    def test_endpoint_requires_authentication(self):
        response = self.client.post(
            reverse("ai_assistant:generate"),
            data='{"message": "Hello"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_empty_message_is_rejected_without_calling_provider(self):
        user = User.objects.create_user("ai-user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.post(
            reverse("ai_assistant:generate"),
            data='{"message": "   "}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.ai_assistant.views.generate_ai_reply")
    def test_history_is_forwarded_to_ai_service(self, mocked_reply):
        mocked_reply.return_value = "Contextual answer"
        user = User.objects.create_user("history-user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.post(
            reverse("ai_assistant:generate"),
            data=(
                '{"message":"Continue","history":'
                '[{"role":"user","content":"Earlier question"},'
                '{"role":"assistant","content":"Earlier answer"}]}'
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        mocked_reply.assert_called_once_with(
            "Continue",
            history=[
                {"role": "user", "content": "Earlier question"},
                {"role": "assistant", "content": "Earlier answer"},
            ],
        )
