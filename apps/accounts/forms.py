from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "autocomplete": "username", "autofocus": True,
            "placeholder": "Enter your username",
        })
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password",
            "placeholder": "Enter your password",
        }),
    )
    remember_me = forms.BooleanField(
        required=False, initial=True, label="Keep me signed in"
    )

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(max_length=80, label="Your name")

    class Meta:
        model = User
        fields = ("display_name", "username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "display_name": "Your display name",
            "username": "Choose a username",
            "email": "you@example.com",
            "password1": "Create a strong password",
            "password2": "Enter your password again",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("placeholder", placeholders.get(name, ""))
            field.widget.attrs.setdefault("autocomplete", {
                "display_name": "name", "username": "username", "email": "email",
                "password1": "new-password", "password2": "new-password",
            }.get(name, "off"))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.display_name = self.cleaned_data["display_name"].strip()
            user.profile.save(update_fields=["display_name"])
        return user

class ProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = (
            "display_name", "avatar", "bio",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.email = self.cleaned_data["email"]
        if commit:
            profile.user.save(update_fields=["email"])
            profile.save()
        return profile

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        users = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.user_id:
            users = users.exclude(pk=self.instance.user_id)
        if users.exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Profile image must be smaller than 5 MB.")
        return avatar


class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "last_seen_visibility", "desktop_notifications",
            "notification_sounds",
        )


class ChatSettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("chat_theme", "chat_wallpaper", "custom_chat_wallpaper")
        labels = {"custom_chat_wallpaper": "Upload wallpaper from this device"}

    def clean_custom_chat_wallpaper(self):
        wallpaper = self.cleaned_data.get("custom_chat_wallpaper")
        if wallpaper and wallpaper.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Wallpaper must be smaller than 8 MB.")
        return wallpaper

    def clean(self):
        cleaned = super().clean()
        if (
            cleaned.get("chat_wallpaper") == "custom"
            and not cleaned.get("custom_chat_wallpaper")
            and not self.instance.custom_chat_wallpaper
        ):
            self.add_error(
                "custom_chat_wallpaper",
                "Choose an image before selecting Custom image.",
            )
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.cleaned_data.get("custom_chat_wallpaper"):
            profile.chat_wallpaper = "custom"
        if commit:
            profile.save()
        return profile


class AppearanceSettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("app_theme",)
