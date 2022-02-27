from django.urls import path
from server.game_handler import consumers

websocket_urlpatterns = [
    path('ws/player/<uuid:room_token>', consumers.PlayerConsumer.as_asgi())
]
