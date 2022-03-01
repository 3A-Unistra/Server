"""
ASGI config for servers project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django_asgi_app = get_asgi_application()

from .game_handler.middlewares import JWTAuthMiddleware
import game_handler.routing
from channels.routing import ProtocolTypeRouter, ChannelNameRouter, URLRouter
from .game_handler.consumers import GameConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(game_handler.routing.websocket_urlpatterns)
        )
    ),

    "channel": ChannelNameRouter({
        'game_engine': GameConsumer.as_asgi()
    })
})
