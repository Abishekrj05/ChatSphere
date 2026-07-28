from django import forms
from django.contrib.auth.models import User
from .models import Conversation, Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("content", "image", "document", "voice_note")

    def clean(self):
        cleaned_data = super().clean()
        if not any(
            cleaned_data.get(field)
            for field in ("content", "image", "document", "voice_note")
        ):
            raise forms.ValidationError("Enter a message or attach a file.")

        limits = {
            "image": 10 * 1024 * 1024,
            "document": 25 * 1024 * 1024,
            "voice_note": 15 * 1024 * 1024,
        }
        for field, limit in limits.items():
            upload = cleaned_data.get(field)
            if upload and upload.size > limit:
                self.add_error(
                    field,
                    f"The selected file must be smaller than {limit // (1024 * 1024)} MB.",
                )
        document = cleaned_data.get("document")
        if document and document.name.lower().endswith(
            (".exe", ".msi", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".scr")
        ):
            self.add_error("document", "This file type is not allowed for security reasons.")
        return cleaned_data

class GroupConversationForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Conversation
        fields = (
            "name", "description", "image", "participants",
            "members_can_send", "members_can_edit_info",
        )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = User.objects.all()
        if current_user:
            queryset = queryset.exclude(pk=current_user.pk)
        self.fields["participants"].queryset = queryset.order_by("username")

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("A group name is required.")
        return name

    def clean_participants(self):
        participants = self.cleaned_data["participants"]
        if not participants:
            raise forms.ValidationError("Select at least one other member.")
        return participants
