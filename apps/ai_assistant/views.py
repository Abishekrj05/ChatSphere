import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from .services import AIServiceError, generate_ai_reply

@login_required
def assistant(request):
    return render(request, "ai_assistant/assistant.html")

@login_required
@require_POST
def generate_reply(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])

    if not message:
        return JsonResponse({"error": "Message is required."}, status=400)

    try:
        reply = generate_ai_reply(
            message,
            history=history if isinstance(history, list) else [],
        )
    except AIServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=503)

    return JsonResponse({"reply": reply})
