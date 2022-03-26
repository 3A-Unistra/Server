import logging
from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .data.exceptions import PacketException
from .data.packets import PacketUtils, PlayerPacket, \
    ExceptionPacket, InternalCheckPlayerValidity, PlayerValid, \
    PlayerDisconnect, InternalPacket, InternalPlayerDisconnect, \
    CreateGame, DeleteRoom, InternalLobbyConnect, LobbyPacket
from .engine import Engine

log = logging.getLogger(__name__)


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer between Client and Server
    """
    player_token: str = None
    game_token: str = None
    valid: bool = False

    async def connect(self):
        # User is anonymous
        if self.scope["user"] is None:
            # Reject the connection
            return await self.close(code=4000)

        self.valid = False

        if 'game_token' in self.scope['url_route']['kwargs']:
            self.game_token = self.scope['url_route']['kwargs']['game_token']

        if self.game_token is None:
            return await self.close(code=4001)

        """
        Player connects -> send internal check player validity to server
        Server respond with same packet
        If not valid, connection is closed
        If valid, packet PlayerValid is sent to WebSocket
        """

        self.player_token = self.scope['user'].id

        packet = InternalCheckPlayerValidity(
            player_token=self.player_token)

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

        # Internal packets are not accepted
        if isinstance(packet, InternalPacket):
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
        self.valid = False

        if 4100 <= code <= 4101:
            return

        # Remove player from broadcast group
        await self.channel_layer.group_discard(self.game_token,
                                               self.channel_name)

        # Handle client-side errors

        packet = InternalPlayerDisconnect(
            reason="client",
            player_token=self.player_token
        )

        await self.channel_layer.send(
            'game_engine',
            {
                'type': 'process.packets',
                'content': packet.serialize(),
                'game_token': self.game_token,
                'channel_name': self.channel_name
            }
        )

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

        # If PlayerDisconnect received, force WebSocket close.
        if isinstance(packet, PlayerDisconnect):
            if packet.player_token == self.player_token:
                return await self.close(code=4101)

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


class LobbyConsumer(AsyncJsonWebsocketConsumer):
    player_token: str = None
    game_token: str = None

    async def connect(self):
        # User is anonymous
        if self.scope["user"] is None:
            # Reject the connection
            return await self.close(code=4000)

        self.player_token = self.scope['user'].id

        # sending the internal packet to the EngineConsumer
        # TODO: in response, we should send the list of the room status
        packet = InternalLobbyConnect(
            player_token=self.player_token)

        # adding player to the lobby group
        async_to_sync(self.channel_layer.group_add)("lobby", self.channel_name)

        # send to game engine worker
        await self.channel_layer.send(
            'game_engine',
            {
                'type': 'process.lobby.packets',
                'content': packet.serialize(),
                'channel_name': self.channel_name
            }
        )

    async def receive_json(self, content, **kwargs):
        try:
            packet = PacketUtils.deserialize_packet(content)
        except PacketException:
            # send error packet (or ignore)
            return

        if isinstance(packet, InternalPacket):
            return

        # send to game engine consumer
        # TODO: game engine consumer must handle the packets
        await self.channel_layer.send(
            'game_engine',
            {
                'type': 'process.lobby.packets',
                'content': packet.serialize(),
                'channel_name': self.channel_name
            }
        )

    async def disconnect(self, code):
        # removing player from the lobby group
        async_to_sync(self.channel_layer.group_discard)("lobby",
                                                        self.channel_name)

        # if game_token != None; send internalplayerdisconnect to engine
        # to remove player?
        return

    async def send_lobby_packet(self, content):
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

    def process_lobby_packet(self, content):
        """
        lobby packets are handled here
        """
        try:
            packet = PacketUtils.deserialize_packet(content)
        except PacketException:
            # send error packet (or ignore)
            return

        # if internal packet:
        if isinstance(packet, InternalLobbyConnect):
            # TODO: send info about all the rooms
            self.engine.send_all_lobby_status(player_token=packet.player_token)

        if not isinstance(packet, LobbyPacket):
            return

        if isinstance(packet, CreateGame):
            self.engine.create_game(packet)

        if isinstance(packet, DeleteRoom):
            self.engine.delete_room(packet)

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
