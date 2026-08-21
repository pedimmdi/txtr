"""
ASGI config for core project.

Exposes the ASGI callable as a module-level variable named ``application``.
Supports HTTP (Django) and WebSocket (Channels).
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()

from core.consumers import PingConsumer, DMConsumer  # noqa: E402

websocket_urlpatterns = [
    path('ws/ping/', PingConsumer.as_asgi()),
    path('ws/dm/<str:username>/', DMConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
