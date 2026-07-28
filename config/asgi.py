import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application
django_asgi_application = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from config.routing import websocket_urlpatterns
from websocket.authentication import SessionAuthMiddlewareStack

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": SessionAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
