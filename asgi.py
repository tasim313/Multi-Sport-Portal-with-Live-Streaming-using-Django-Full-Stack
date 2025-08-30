import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from sports.consumers import MatchConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sports_portal.settings')

django_asgi_app = get_asgi_application()

# WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/matches/<int:match_id>/', MatchConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})