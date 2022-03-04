import logging

from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .data.exceptions import PacketException
from .data.packets import PacketUtils

log = logging.getLogger(__name__)


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer between Client and Server
    """
    room_token: str

    async def connect(self):
        pass

    """
    Receiving packets from client, checking if packet is valid.
    """

    async def receive_json(self, content, **kwargs):
        """
        1. Deserializing packet
        2. Check packet validity
        3. Process local player packets
        4. Reserialize to send only relevant variables
        5. Send to game_engine consumer
        """

        try:
            packet = PacketUtils.deserialize_packet(content)
        except PacketException:
            # send error packet (or ignore)
            return

        # process packets here

        # send to game engine worker
        await self.channel_layer.send(
            'game_engine',
            {
                'type': 'game.process',
                'packet': packet.serialize()
            }
        )

        async def disconnect(self, code):
            pass

    class GameConsumer(SyncConsumer):
        """
        Consumer between Game Worker and PlayerConsumer
        """

        def __init__(self):
            pass

        def game_process(self, packet):
            pass
