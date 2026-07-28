from apps.chat.routing import websocket_urlpatterns as chat_patterns
from apps.notifications.routing import websocket_urlpatterns as notification_patterns

websocket_urlpatterns = chat_patterns + notification_patterns
