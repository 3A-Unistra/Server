from django.urls import path
from server.game_handler import consumers

websocket_urlpatterns = [
    path('ws/game/<uuid:room_token>/<uuid:player_token>',
         consumers.PlayerConsumer.as_asgi())
]
