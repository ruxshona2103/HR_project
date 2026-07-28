"""
ASGI config for config project.
Production and Development ASGI configuration including Django Channels (WebSocket).
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from .middleware import TokenAuthMiddlewareStack
import apps.ai_engine.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddlewareStack(
        URLRouter(
            apps.ai_engine.routing.websocket_urlpatterns
        )
    ),
})