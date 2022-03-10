from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import uuid
from enum import Enum
from threading import Thread
from queue import Queue

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
import pause

from server.game_handler.data import Board, Player
from server.game_handler.data.exceptions.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import Packet, GameStart, AppletReady, \
    PlayerPacket, ExceptionPacket, InternalCheckPlayerValidity

"""
States:
-> Démarrage -> démarrage timer remplacement joueur par un bot.
-> Attente de nb_joueurs AppletReady
-> Lorsque ce nombre est atteint => GameStart
-> On attends 2-3 secondes
-> On envoie un paquet GameStartDice

"""


class GameState(Enum):
    STOP_THREAD = -2
    OFFLINE = -1
    LOBBY = 0
    WAITING_PLAYERS = 1
    STARTING = 2
    START_DICE = 3


@dataclass
class QueuePacket:
    packet: Packet
    channel_name: str


class Game(Thread):
    uid: str
    state: GameState
    board: Board
    packets_queue: Queue
    current_tick: int
    timeout: datetime
    start_date: datetime
    CONFIG: {}
    # reference to games dict
    games: {}

    def __init__(self, uid: str = str(uuid.uuid4()), **kwargs):
        super(Game, self).__init__(daemon=True, name="Game_%s" % uid, **kwargs)
        self.channel_layer = get_channel_layer()
        self.uid = uid
        self.state = GameState.WAITING_PLAYERS
        self.packets_queue = Queue()
        self.current_tick = 0
        self.CONFIG = getattr(settings, "ENGINE_CONFIG", None)
        self.tick_duration = 1.0 / self.CONFIG.get('TICK_RATE')
        self.board = Board()

    def run(self) -> None:
        # Starting game thread
        self.state = GameState.WAITING_PLAYERS
        # Set start date
        self.start_date = datetime.now()

        # while state is not stop thread
        while self.state is not GameState.STOP_THREAD:
            # get unix time in seconds before tick processing
            start = time.time()

            # process game tick
            self.tick()

            # sleep until(start + tick_duration)
            # To reduce tick loss if tick processing is too long
            pause.until(start + self.tick_duration)

        # execute last func before stop
        self.proceed_stop()

    def tick(self):
        """
        Main function: every tick, this function will be executed
        """

        # Blocking queue
        self.packets_queue.join()

        # Store all packets in temp array
        # If packet processing is taking too much time,
        # The queue will be locked for a too long period
        packets = []

        while not self.packets_queue.empty():
            packets.append(self.packets_queue.get(block=False))

        # Unblock
        self.packets_queue.task_done()

        # Process all packets in queue
        for packet in packets:
            self.process_packet(packet)

        # Do logic here
        self.process_logic()

    def process_packet(self, queue_packet: QueuePacket):
        packet: Packet = queue_packet.packet

        # check player validity
        if isinstance(packet, InternalCheckPlayerValidity):
            exists = self.board.player_exists(packet.player_token)
            self.send_packet(
                channel_name=queue_packet.channel_name,
                packet=InternalCheckPlayerValidity(player_token='',
                                                   valid=exists))
            if not exists:
                return

        if self.state is GameState.LOBBY:
            if isinstance(packet, GameStart):
                # set state to waiting players
                # the server will wait AppletReady packets.
                self.state = GameState.WAITING_PLAYERS
                self.timeout = datetime.now() + timedelta(
                    seconds=self.CONFIG.get('WAITING_PLAYERS_TIMEOUT'))
        else:
            # If state is not lobby
            # Check for packet validity
            if isinstance(packet, PlayerPacket):
                if not self.board.player_exists(packet.player_token):
                    return self.send_packet(
                        channel_name=queue_packet.channel_name,
                        packet=ExceptionPacket(code=4100))

        if self.state is GameState.WAITING_PLAYERS:
            # WebGL app is ready to play
            if isinstance(packet, AppletReady):
                player = self.board.get_player(packet.player_token)

                if player is None:
                    return self.send_packet(
                        channel_name=queue_packet.channel_name,
                        packet=ExceptionPacket(code=4100))
                else:
                    player.connect()

    def proceed_stop(self):
        # Delete game
        del self.games[self.uid]

    def process_logic(self):
        # State is waiting that players connecting and send AppletReady
        if self.state is GameState.WAITING_PLAYERS:
            if self.board.get_online_players_count() == self.board.players_nb:
                # We can start the game
                self.start_game()
            elif self.timeout < datetime.now():  # Check timeout
                if self.board.get_online_real_players_count() == 0:
                    # After timeout, if no one is connected
                    # Stop game
                    self.state = GameState.STOP_THREAD
                    return
                else:
                    self.start_game()

    def start_game(self):
        # Set bot names to all players
        self.board.set_bot_names()
        self.state = GameState.STARTING
        self.timeout = datetime.now() + timedelta(
            seconds=self.CONFIG.get('GAME_STARTING_TIMEOUT'))
        self.broadcast_packet(GameStart())

    def broadcast_packet(self, packet: Packet):
        async_to_sync(self.channel_layer.group_send)(
            self.uid, {"type": "game_update", "packet": packet.serialize()}
        )

    def send_packet_to_player(self, player: Player, packet: Packet):
        if player.bot is True:
            return
        self.send_packet(player.channel_name, packet)

    def send_packet(self, channel_name: str, packet: Packet):
        """
        Send packet to channel layer
        :param channel_name: Channel to send packet to
        :param packet: Packet to send
        """
        if channel_name is None:
            return

        async_to_sync(self.channel_layer.send)(
            channel_name, {
                'type': 'player.callback',
                'packet': packet.serialize()
            })


class Engine:
    games: dict[str, Game]

    def __init__(self, **kwargs):
        self.games = {}

    def add_game(self, game: Game):
        """
        Add a game to active games list
        :param game: Game to add
        """
        if game.uid in self.games:
            return

        # Reference to games dict (delete game)
        game.games = self.games

        self.games[game.uid] = game

        # start thread only if state is offline
        if game.state is not GameState.OFFLINE:
            return

        # Start thread
        game.start()

    def remove_game(self, uid: str):
        """
        Remove a game from active games list
        :param uid: UUID of an existing game
        """

        if uid not in self.games:
            raise GameNotExistsException()

        game = self.games[uid]

        # Game should be stop thread
        game.state = GameState.STOP_THREAD

        del self.games[uid]

    def send_packet(self, game_uid: str, packet: Packet,
                    channel_name: str = None):
        """
        Add packet to game packets queue
        Blocking thread until packet is added to queue
        :param game_uid: UUID of an existing game
        :param packet: Packet to send
        :param channel_name: Channel name (to contact player)
        """
        if game_uid not in self.games:
            raise GameNotExistsException()

        # Blocking function that adds packet to queue
        self.games[game_uid].packets_queue.put(
            QueuePacket(packet=packet, channel_name=channel_name))
