from django.urls import path
from server.game_handler import consumers

websocket_urlpatterns = [
    path('ws/game/<uuid:game_token>', consumers.PlayerConsumer.as_asgi()),
    path('ws/lobby', consumers.LobbyConsumer.as_asgi())
]
