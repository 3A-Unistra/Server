"""
ASGI config for servers project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from .game_handler.middlewares import AuthMiddleware
from channels.routing import ProtocolTypeRouter, ChannelNameRouter, URLRouter
from .game_handler.consumers import GameEngineConsumer
from .game_handler import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AuthMiddleware(
        URLRouter(routing.websocket_urlpatterns)
    ),

    "channel": ChannelNameRouter({
        "game_engine": GameEngineConsumer.as_asgi()
    })
})
