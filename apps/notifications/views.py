from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

def notification_context(request):
    if not request.user.is_authenticated:
        return {"unread_notification_count": 0}

    return {
        "unread_notification_count": request.user.chat_notifications.filter(
            is_read=False
        ).count()
    }

@login_required
def unread_count(request):
    count = request.user.chat_notifications.filter(is_read=False).count()
    return JsonResponse({"unread_count": count})

@login_required
@require_POST
def mark_all_read(request):
    request.user.chat_notifications.filter(is_read=False).update(is_read=True)
    return redirect("chat:dashboard")

@login_required
def notification_list(request):
    notifications = request.user.chat_notifications.select_related(
        "conversation"
    )[:100]
    return render(
        request,
        "notifications/list.html",
        {"notifications": notifications},
    )

@login_required
def open_notification(request, notification_id):
    notification = get_object_or_404(
        request.user.chat_notifications.select_related("conversation"),
        pk=notification_id,
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    conversation = notification.conversation
    if not conversation:
        return redirect("notifications:list")
    if not conversation.participants.filter(pk=request.user.pk).exists():
        return redirect("notifications:list")
    route = "chat:group_room" if conversation.is_group else "chat:room"
    return redirect(route, conversation_id=conversation.pk)
