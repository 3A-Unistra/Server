import logging

from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .data.exceptions import PacketException
from .data.packets import PacketUtils
from .engine import Engine

log = logging.getLogger(__name__)


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer between Client and Server
    """
    game_token: str

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
                'type': 'process.packets',
                'content': packet.serialize(),
                'game_token': self.game_token
            }
        )

        async def disconnect(self, code):
            pass

    class GameEngineConsumer(SyncConsumer):
        """
        Consumer between Game Engine Worker and PlayerConsumer
        starts consumer when first request is made to game consumer
        """
        engine: Engine

        def __init__(self):
            self.engine = Engine()
            log.info("Starting engine thread")

        def process_packets(self, content):
            """
            Only packets for existing games are processed here
            :param content: JSON received from PlayerConsumer
            """
            try:
                packet = PacketUtils.deserialize_packet(content)
            except PacketException:
                # send error packet (or ignore)
                return

            # Check if packet is None and game token exists
            if packet is None or 'game_token' not in content:
                return

            game_token = content['game_token']

            # Send packet to game thread
            self.engine.send_packet(game_uid=game_token, packet=packet)

        def process_game_management(self, content):
            """
            Only actions from Lobby Worker are received here
            :param content: JSON received from LobbyConsumer
            """

            # TODO: Maybe process new type of packets here [only lobby packets]?
            pass
