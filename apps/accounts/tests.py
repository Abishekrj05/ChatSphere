from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

class AccountsTests(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_profile_is_created_with_user(self):
        user = User.objects.create_user(username="tester", password="StrongPass123")
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.name, "tester")

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="person@example.com",
            password="StrongPass123",
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newperson",
                "display_name": "New Person",
                "email": "PERSON@example.com",
                "password1": "DifferentStrongPass123",
                "password2": "DifferentStrongPass123",
            },
        )
        self.assertContains(response, "This email is already registered.")
        self.assertFalse(User.objects.filter(username="newperson").exists())

    def test_registration_saves_display_name(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "named-user",
                "display_name": "Abishek RJ",
                "email": "named@example.com",
                "password1": "DifferentStrongPass123",
                "password2": "DifferentStrongPass123",
            },
        )
        self.assertRedirects(response, reverse("chat:dashboard"))
        user = User.objects.get(username="named-user")
        self.assertEqual(user.profile.display_name, "Abishek RJ")

    def test_profile_edit_updates_email_and_bio(self):
        user = User.objects.create_user(
            username="editor",
            email="old@example.com",
            password="StrongPass123",
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {"email": "new@example.com", "bio": "Updated bio"},
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        user.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.profile.bio, "Updated bio")

    def test_logout_redirects_to_welcome_page(self):
        user = User.objects.create_user(
            username="logout-user",
            password="StrongPass123",
        )
        self.client.force_login(user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("chat:welcome"))

    def test_login_without_remember_me_uses_browser_session(self):
        user = User.objects.create_user("session-user", password="StrongPass123")
        response = self.client.post(
            reverse("accounts:login"),
            {"username": user.username, "password": "StrongPass123"},
        )
        self.assertRedirects(response, reverse("chat:dashboard"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_rejects_unsafe_next_redirect(self):
        user = User.objects.create_user("safe-user", password="StrongPass123")
        response = self.client.post(
            reverse("accounts:login") + "?next=https://unsafe.example/",
            {
                "username": user.username,
                "password": "StrongPass123",
                "remember_me": "on",
                "next": "https://unsafe.example/",
            },
        )
        self.assertRedirects(response, reverse("chat:dashboard"))

    def test_chat_and_appearance_settings_are_saved(self):
        user = User.objects.create_user("theme-user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.post(
            reverse("accounts:settings", args=["chat"]),
            {"chat_theme": "blue", "chat_wallpaper": "soft"},
        )
        self.assertRedirects(
            response, reverse("accounts:settings", args=["chat"])
        )
        response = self.client.post(
            reverse("accounts:settings", args=["appearance"]),
            {"app_theme": "dark"},
        )
        self.assertRedirects(
            response, reverse("accounts:settings", args=["appearance"])
        )
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.chat_theme, "blue")
        self.assertEqual(user.profile.chat_wallpaper, "soft")
        self.assertEqual(user.profile.app_theme, "dark")

    def test_blocked_contact_can_be_unblocked_from_privacy(self):
        user = User.objects.create_user("privacy-user", password="StrongPass123")
        blocked = User.objects.create_user("blocked-user", password="StrongPass123")
        user.profile.blocked_users.add(blocked)
        self.client.force_login(user)
        response = self.client.post(
            reverse("accounts:unblock_user", args=[blocked.pk])
        )
        self.assertRedirects(
            response, reverse("accounts:settings", args=["privacy"])
        )
        self.assertFalse(user.profile.blocked_users.filter(pk=blocked.pk).exists())
