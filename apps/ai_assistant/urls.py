from django.urls import path
from .views import assistant, generate_reply

app_name = "ai_assistant"

urlpatterns = [
    path("", assistant, name="assistant"),
    path("generate/", generate_reply, name="generate"),
]
