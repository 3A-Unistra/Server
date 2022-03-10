import logging

from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .data.exceptions import PacketException
from .data.packets import PacketUtils, LobbyPacket, GameStart
from .engine import Engine

log = logging.getLogger(__name__)


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer between Client and Server
    """
    game_token: str

    async def connect(self):

        # User is anonymous
        if self.scope["user"] is None:
            # Reject the connection
            return await self.close()

        # TODO: Handle connection

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

    async def player_callback(self, content):
        """
        When player gets packet from engine, this function is called
        GameEngine -> PlayerConsumer -> WebGL
        """
        packet = content.get('packet', None)

        if packet is None:
            return

        try:
            packet = PacketUtils.deserialize_packet(content)
        except PacketException:
            # send error packet (or ignore)
            return

        # TODO: Manage errors that closes WebSocket
        if isinstance(packet, PacketException):
            pass

        # Send packet to front/cli
        await self.send(packet.serialize())

    async def send_packet(self, content):
        """
        When group [game uid] broadcasts, this function is called
        GameEngine -> PlayerConsumer -> WebGL
        """
        packet = content.get('packet', None)

        if packet is None:
            return

        await self.send_json(packet)


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

        # Check if packet is not None and game token exists
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
        try:
            packet = PacketUtils.deserialize_packet(content)
        except PacketException:
            # send error packet (or ignore)
            return

        # Check if packet is not None
        if packet is None:
            return

        # Check if packet is a lobby packet
        if not isinstance(packet, LobbyPacket):
            return

        # Process start packet

        if isinstance(packet, GameStart):
            # Check if packet is gamestart
            pass

        # TODO: Maybe process new type of lobby packets here?
        pass
