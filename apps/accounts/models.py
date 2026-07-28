from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    LAST_SEEN_CHOICES = (("everyone", "Everyone"), ("contacts", "Contacts"), ("nobody", "Nobody"))
    CHAT_THEME_CHOICES = (
        ("green", "Classic green"), ("blue", "Ocean blue"),
        ("purple", "Soft purple"), ("sand", "Warm sand"),
    )
    WALLPAPER_CHOICES = (
        ("doodle", "Chat doodles"), ("plain", "Plain"),
        ("soft", "Soft gradient"), ("dark", "Dark pattern"),
        ("custom", "Custom image"),
    )
    APP_THEME_CHOICES = (
        ("system", "Use system setting"), ("light", "Light"), ("dark", "Dark"),
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )
    display_name = models.CharField(max_length=80, blank=True)
    bio = models.CharField(max_length=160, blank=True)
    is_online = models.BooleanField(default=False)
    active_connections = models.PositiveIntegerField(default=0)
    last_seen = models.DateTimeField(blank=True, null=True)
    last_seen_visibility = models.CharField(max_length=12, choices=LAST_SEEN_CHOICES, default="everyone")
    desktop_notifications = models.BooleanField(default=True)
    notification_sounds = models.BooleanField(default=True)
    chat_theme = models.CharField(max_length=12, choices=CHAT_THEME_CHOICES, default="green")
    chat_wallpaper = models.CharField(max_length=12, choices=WALLPAPER_CHOICES, default="doodle")
    custom_chat_wallpaper = models.ImageField(
        upload_to="chat_wallpapers/", blank=True, null=True
    )
    app_theme = models.CharField(max_length=12, choices=APP_THEME_CHOICES, default="system")
    blocked_users = models.ManyToManyField(
        User, blank=True, related_name="blocked_by_profiles"
    )

    def __str__(self):
        return self.user.username

    @property
    def name(self):
        return (
            self.display_name.strip()
            or self.user.get_full_name().strip()
            or self.user.username
        )
