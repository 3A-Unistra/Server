import logging

from channels.consumer import SyncConsumer

log = logging.getLogger(__name__)


class GameConsumer(SyncConsumer):
    def __init__(self):
        pass
