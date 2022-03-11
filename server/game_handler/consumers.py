import logging
from urllib.parse import parse_qs

from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .data.exceptions import PacketException
from .data.packets import PacketUtils, LobbyPacket, GameStart, PlayerPacket, \
    ExceptionPacket, InternalCheckPlayerValidity, PlayerValid
from .engine import Engine

log = logging.getLogger(__name__)


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer between Client and Server
    """
    game_token: str
    player_token: str
    valid: bool

    async def connect(self):

        # User is anonymous
        if self.scope["user"] is None:
            # Reject the connection
            return await self.close(code=4000)

        self.valid = False

        query = parse_qs(self.scope["query_string"].decode("utf8"))
        game_token = None

        if 'game_token' in self.scope['url_route']['kwargs']:
            game_token = self.scope['url_route']['kwargs']['game_token']

        player_token = query.get('player_token', None)

        if game_token is None:
            return await self.close(code=4001)

        if player_token is None:
            return await self.close(code=4002)

        player_token = player_token[0]

        """
        Player connects -> send internal check player validity to server
        Server respond with same packet
        If not valid, connection is closed
        If valid, packet PlayerValid is sent to WebSocket
        """

        packet = InternalCheckPlayerValidity(player_token=player_token)

        # send to game engine worker
        await self.channel_layer.send(
            'game_engine',
            {
                'type': 'process.packets',
                'content': packet.serialize(),
                'game_token': self.game_token,
                'channel_name': self.channel_name
            }
        )

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

        # Refuse if connection is not valid
        if not self.valid:
            return

        try:
            packet = PacketUtils.deserialize_packet(content)
        except PacketException:
            # send error packet (or ignore)
            return

        # process packets here
        if isinstance(packet, PlayerPacket):
            packet.player_token = self.player_token

        # send to game engine worker
        await self.channel_layer.send(
            'game_engine',
            {
                'type': 'process.packets',
                'content': packet.serialize(),
                'game_token': self.game_token,
                'channel_name': self.channel_name
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
        if isinstance(packet, ExceptionPacket):
            # Player invalid closing connection
            if packet.code == 4100:
                self.valid = False
                return await self.close(code=4100)

        # Send validity token
        if isinstance(packet, InternalCheckPlayerValidity):
            if packet.valid:
                packet = PlayerValid()

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

        # get channel name
        channel_name = content[
            'channel_name'] if 'channel_name' in content else ''

        # Send packet to game thread
        self.engine.send_packet(game_uid=game_token, packet=packet,
                                channel_name=channel_name)

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
