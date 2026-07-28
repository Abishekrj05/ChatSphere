import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.html import strip_tags
from apps.notifications.services import notify_message
from .forms import GroupConversationForm, MessageForm
from .models import Conversation, ConversationPreference, Message, MessageReaction
from .services import create_message, get_or_create_private_conversation, mark_messages_read, messaging_error, serialize_message
from .utils import conversation_title
from .utils import user_display_name

def welcome(request):
    if request.user.is_authenticated:
        return redirect("chat:dashboard")
    return render(request, "chat/welcome.html")

def build_conversation_cards(user):
    conversations = (
        user.conversations
        .prefetch_related("participants__profile", "messages")
        .order_by("-updated_at")
    )
    cards = [
        {
            "conversation": conversation,
            "title": conversation_title(conversation, user),
            "other": (
                None if conversation.is_group
                else conversation.other_participant(user)
            ),
            "last_message": conversation.messages.exclude(hidden_for=user).last(),
            "preference": ConversationPreference.objects.filter(
                conversation=conversation, user=user
            ).first(),
        }
        for conversation in conversations
    ]
    for card in cards:
        count = card["conversation"].messages.filter(
            receipts__user=user, receipts__read_at__isnull=True
        ).count()
        card["unread_count"] = max(
            count, 1 if card["preference"] and card["preference"].marked_unread else 0
        )
    return sorted(
        cards,
        key=lambda card: bool(card["preference"] and card["preference"].is_pinned),
        reverse=True,
    )

def broadcast_conversation_event(conversation_id, event):
    async_to_sync(get_channel_layer().group_send)(
        f"chat_{conversation_id}",
        {"type": "chat.event", "event": event},
    )

@login_required
def dashboard(request):
    users = (
        User.objects.exclude(pk=request.user.pk)
        .select_related("profile")
        .order_by("username")
    )

    return render(
        request,
        "chat/dashboard.html",
        {
            "conversation_cards": build_conversation_cards(request.user),
            "users": users,
        },
    )

@login_required
def start_private_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        return redirect("chat:dashboard")

    conversation = get_or_create_private_conversation(
        request.user,
        other_user,
    )
    return redirect("chat:room", conversation_id=conversation.pk)

@login_required
def room(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related(
            "participants__profile",
            "messages__sender",
        ),
        pk=conversation_id,
        participants=request.user,
        is_group=False,
    )

    for event in mark_messages_read(conversation, request.user):
        broadcast_conversation_event(conversation.pk, event)
    request.user.chat_notifications.filter(conversation=conversation).update(is_read=True)
    ConversationPreference.objects.filter(
        conversation=conversation, user=request.user
    ).update(marked_unread=False)

    other_user = conversation.other_participant(request.user)
    visibility = other_user.profile.last_seen_visibility
    can_view_presence = visibility == "everyone" or (
        visibility == "contacts"
        and Conversation.private_between(request.user, other_user) is not None
    )
    return render(
        request,
        "chat/room.html",
        {
            "conversation": conversation,
            "chat_messages": conversation.messages.exclude(hidden_for=request.user).filter(
                created_at__gt=(
                    ConversationPreference.objects.filter(
                        conversation=conversation, user=request.user
                    ).values_list("cleared_at", flat=True).first() or conversation.created_at
                )
            ),
            "other_user": other_user,
            "can_view_presence": can_view_presence,
            "conversation_cards": build_conversation_cards(request.user),
            "active_conversation_id": conversation.pk,
            "active_preference": ConversationPreference.objects.filter(
                conversation=conversation, user=request.user
            ).first(),
            "pinned_message": conversation.messages.filter(
                pinned_at__isnull=False,
                is_deleted=False,
            ).select_related("sender__profile").order_by("-pinned_at").first(),
        },
    )

@login_required
def group_room(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related(
            "participants__profile",
            "messages__sender",
        ),
        pk=conversation_id,
        participants=request.user,
        is_group=True,
    )

    for event in mark_messages_read(conversation, request.user):
        broadcast_conversation_event(conversation.pk, event)
    request.user.chat_notifications.filter(conversation=conversation).update(is_read=True)
    ConversationPreference.objects.filter(
        conversation=conversation, user=request.user
    ).update(marked_unread=False)

    return render(
        request,
        "chat/group_room.html",
        {
            "conversation": conversation,
            "chat_messages": conversation.messages.exclude(hidden_for=request.user).filter(
                created_at__gt=(
                    ConversationPreference.objects.filter(
                        conversation=conversation, user=request.user
                    ).values_list("cleared_at", flat=True).first() or conversation.created_at
                )
            ),
            "conversation_cards": build_conversation_cards(request.user),
            "active_conversation_id": conversation.pk,
            "active_preference": ConversationPreference.objects.filter(
                conversation=conversation, user=request.user
            ).first(),
            "participant_names": ", ".join(
                user_display_name(member)
                for member in conversation.participants.all()
            ),
            "invite_url": request.build_absolute_uri(
                f"/groups/join/{conversation.ensure_invite_code()}/"
            ) if conversation.created_by_id == request.user.pk else "",
            "pinned_message": conversation.messages.filter(
                pinned_at__isnull=False,
                is_deleted=False,
            ).select_related("sender__profile").order_by("-pinned_at").first(),
        },
    )

@login_required
@require_POST
def send_attachment(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id,
        participants=request.user,
    )
    form = MessageForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    permission_error = messaging_error(conversation, request.user)
    if permission_error:
        return JsonResponse({"error": permission_error}, status=403)

    message = create_message(
        conversation,
        request.user,
        form.cleaned_data.get("content", "").strip(),
        reply_to=conversation.messages.filter(
            pk=request.POST.get("reply_to")
        ).first() if request.POST.get("reply_to") else None,
        image=form.cleaned_data.get("image"),
        document=form.cleaned_data.get("document"),
        voice_note=form.cleaned_data.get("voice_note"),
    )
    payload = serialize_message(message)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation.pk}",
        {"type": "chat.message", "message": payload},
    )
    notify_message(message)
    return JsonResponse(payload, status=201)

@login_required
@require_POST
def edit_message(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related("conversation"),
        pk=message_id,
        sender=request.user,
        conversation__participants=request.user,
        is_deleted=False,
    )
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    content = strip_tags(str(payload.get("content", ""))).strip()
    if not content:
        return JsonResponse({"error": "Message text is required."}, status=400)
    message.content = content[:4000]
    message.edited_at = timezone.now()
    message.save(update_fields=["content", "edited_at"])
    event = {
        "action": "edited",
        "message_id": message.pk,
        "content": message.content,
        "edited_at": message.edited_at.isoformat(),
    }
    broadcast_conversation_event(message.conversation_id, event)
    return JsonResponse(event)

@login_required
@require_POST
def delete_message(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related("conversation"),
        pk=message_id,
        conversation__participants=request.user,
    )
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}
    scope = payload.get("scope", "everyone")
    if scope not in {"me", "everyone"}:
        return JsonResponse({"error": "Invalid deletion option."}, status=400)
    if scope == "me":
        message.hidden_for.add(request.user)
        return JsonResponse({
            "action": "hidden", "message_id": message.pk, "scope": "me"
        })
    if message.sender_id != request.user.pk:
        return JsonResponse(
            {"error": "You can only delete this message for yourself."}, status=403
        )
    message.content = ""
    message.is_deleted = True
    message.edited_at = timezone.now()
    message.image.delete(save=False)
    message.document.delete(save=False)
    message.voice_note.delete(save=False)
    message.save(
        update_fields=[
            "content", "is_deleted", "edited_at",
            "image", "document", "voice_note",
        ]
    )
    event = {"action": "deleted", "message_id": message.pk}
    broadcast_conversation_event(message.conversation_id, event)
    return JsonResponse(event)

@login_required
@require_POST
def react_to_message(request, message_id):
    message = get_object_or_404(
        Message,
        pk=message_id,
        conversation__participants=request.user,
        is_deleted=False,
    )
    emoji = request.POST.get("emoji", "")
    if emoji not in MessageReaction.ALLOWED_EMOJIS:
        return JsonResponse({"error": "Unsupported reaction."}, status=400)
    reaction, created = MessageReaction.objects.get_or_create(
        message=message,
        user=request.user,
        emoji=emoji,
    )
    if not created:
        reaction.delete()
    data = serialize_message(
        Message.objects.select_related("sender", "reply_to__sender").get(pk=message.pk)
    )
    event = {
        "action": "reactions",
        "message_id": message.pk,
        "reactions": data["reactions"],
    }
    broadcast_conversation_event(message.conversation_id, event)
    return JsonResponse(event)

@login_required
@require_POST
def toggle_pin_message(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related("conversation"),
        pk=message_id,
        conversation__participants=request.user,
        is_deleted=False,
    )
    if message.conversation.is_group and message.conversation.created_by_id != request.user.pk:
        return JsonResponse({"error": "Only the group owner can pin messages."}, status=403)
    if message.pinned_at:
        message.pinned_at = None
        message.pinned_by = None
    else:
        message.pinned_at = timezone.now()
        message.pinned_by = request.user
    message.save(update_fields=["pinned_at", "pinned_by"])
    event = {
        "action": "pinned",
        "message_id": message.pk,
        "is_pinned": bool(message.pinned_at),
    }
    broadcast_conversation_event(message.conversation_id, event)
    return JsonResponse(event)

@login_required
def create_group(request):
    form = GroupConversationForm(
        request.POST or None,
        request.FILES or None,
        current_user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        conversation = form.save(commit=False)
        conversation.is_group = True
        conversation.created_by = request.user
        conversation.save()
        form.save_m2m()
        conversation.participants.add(request.user)
        messages.success(request, "Group created successfully.")
        return redirect("chat:group_room", conversation_id=conversation.pk)

    return render(request, "chat/search.html", {"group_form": form})

@login_required
def group_settings(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related("participants"),
        pk=conversation_id,
        is_group=True,
        participants=request.user,
    )
    if conversation.created_by_id != request.user.pk:
        messages.error(request, "Only the group owner can manage members.")
        return redirect("chat:group_room", conversation_id=conversation.pk)

    form = GroupConversationForm(
        request.POST or None,
        request.FILES or None,
        instance=conversation,
        current_user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        conversation = form.save()
        conversation.participants.add(request.user)
        messages.success(request, "Group settings updated.")
        return redirect("chat:group_room", conversation_id=conversation.pk)
    return render(
        request,
        "chat/group_settings.html",
        {"conversation": conversation, "form": form},
    )

@login_required
@require_POST
def leave_group(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id,
        is_group=True,
        participants=request.user,
    )
    if conversation.created_by_id == request.user.pk:
        messages.error(
            request,
            "The group owner cannot leave. Transfer ownership or delete the group.",
        )
        return redirect("chat:group_room", conversation_id=conversation.pk)
    conversation.participants.remove(request.user)
    request.user.chat_notifications.filter(conversation=conversation).delete()
    messages.success(request, f"You left {conversation.name}.")
    return redirect("chat:dashboard")

@login_required
@require_POST
def delete_group(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id,
        is_group=True,
        created_by=request.user,
    )
    name = conversation.name
    conversation.delete()
    messages.success(request, f"{name} was deleted.")
    return redirect("chat:dashboard")

@login_required
def search(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.exclude(pk=request.user.pk)

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(profile__display_name__icontains=query)
        )
    else:
        users = users.none()

    matching_messages = Message.objects.none()
    if query:
        matching_messages = (
            Message.objects.filter(
                Q(content__icontains=query)
                | Q(document__icontains=query)
                | Q(image__icontains=query)
                | Q(voice_note__icontains=query),
                conversation__participants=request.user,
                is_deleted=False,
            )
            .exclude(hidden_for=request.user)
            .select_related("conversation", "sender")[:30]
        )

    return render(
        request,
        "chat/search.html",
        {
            "query": query,
            "users": users,
            "matching_messages": matching_messages,
            "group_form": GroupConversationForm(current_user=request.user),
        },
    )


@login_required
@require_POST
def conversation_action(request, conversation_id):
    conversation = get_object_or_404(
        Conversation, pk=conversation_id, participants=request.user
    )
    action = request.POST.get("action", "")
    preference, _ = ConversationPreference.objects.get_or_create(
        conversation=conversation, user=request.user
    )
    fields = {
        "archive": "is_archived", "mute": "is_muted",
        "pin": "is_pinned", "unread": "marked_unread",
    }
    if action in fields:
        field = fields[action]
        setattr(preference, field, not getattr(preference, field))
        preference.save(update_fields=[field])
    elif action == "clear":
        preference.cleared_at = timezone.now()
        preference.save(update_fields=["cleared_at"])
    elif action == "block":
        if conversation.is_group:
            return JsonResponse({"error": "Groups cannot be blocked."}, status=400)
        other = conversation.other_participant(request.user)
        if not other:
            return JsonResponse({"error": "User not found."}, status=404)
        blocked = request.user.profile.blocked_users
        blocked.remove(other) if blocked.filter(pk=other.pk).exists() else blocked.add(other)
    else:
        return JsonResponse({"error": "Unsupported action."}, status=400)
    return JsonResponse({"ok": True, "action": action})


@login_required
@require_POST
def forward_message(request, message_id):
    source = get_object_or_404(
        Message, pk=message_id, conversation__participants=request.user,
        is_deleted=False,
    )
    target = get_object_or_404(
        Conversation, pk=request.POST.get("conversation_id"), participants=request.user
    )
    permission_error = messaging_error(target, request.user)
    if permission_error:
        return JsonResponse({"error": permission_error}, status=403)
    copied_files = {}
    for field_name in ("image", "document", "voice_note"):
        field = getattr(source, field_name)
        if field:
            field.open("rb")
            copied_files[field_name] = ContentFile(
                field.read(), name=field.name.rsplit("/", 1)[-1]
            )
            field.close()
    forwarded = create_message(
        target, request.user, source.content, forwarded_from=source, **copied_files
    )
    payload = serialize_message(forwarded)
    async_to_sync(get_channel_layer().group_send)(
        f"chat_{target.pk}", {"type": "chat.message", "message": payload}
    )
    notify_message(forwarded)
    return JsonResponse(payload, status=201)


@login_required
def message_info(request, message_id):
    message = get_object_or_404(
        Message, pk=message_id, sender=request.user,
        conversation__participants=request.user,
    )
    return JsonResponse({
        "id": message.pk,
        "status": "read" if message.read_at or message.is_read else (
            "delivered" if message.delivered_at else "sent"
        ),
        "sent_at": message.created_at.isoformat(),
        "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
        "read_at": message.read_at.isoformat() if message.read_at else None,
    })


@login_required
def join_group(request, invite_code):
    conversation = get_object_or_404(
        Conversation, invite_code=invite_code, is_group=True
    )
    conversation.participants.add(request.user)
    messages.success(request, f"You joined {conversation.name}.")
    return redirect("chat:group_room", conversation_id=conversation.pk)


@login_required
@require_POST
def regenerate_invite(request, conversation_id):
    conversation = get_object_or_404(
        Conversation, pk=conversation_id, is_group=True, created_by=request.user
    )
    conversation.invite_code = None
    conversation.save(update_fields=["invite_code"])
    code = conversation.ensure_invite_code()
    return JsonResponse({"invite_url": request.build_absolute_uri(
        f"/groups/join/{code}/"
    )})
