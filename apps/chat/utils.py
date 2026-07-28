from django.core.exceptions import ObjectDoesNotExist

def user_display_name(user):
    if not user:
        return ""
    try:
        return user.profile.name
    except (AttributeError, ObjectDoesNotExist):
        return user.get_full_name().strip() or user.username

def conversation_title(conversation, current_user):
    if conversation.is_group:
        return conversation.name or f"Group {conversation.pk}"

    other = conversation.other_participant(current_user)
    return user_display_name(other) if other else "Private conversation"
