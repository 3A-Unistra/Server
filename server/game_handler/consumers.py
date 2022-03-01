import logging

from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

log = logging.getLogger(__name__)


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    pass


class GameConsumer(SyncConsumer):
    def __init__(self):
        pass
