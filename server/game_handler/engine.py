import time
import uuid
from enum import Enum
from threading import Thread
from queue import Queue
from channels.layers import get_channel_layer
from django.conf import settings

from server.game_handler.data import Board
from server.game_handler.data.exceptions.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import Packet

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
    WAITING_PLAYERS = 0
    STARTING = 1
    START_DICE = 2


class Game(Thread):
    uid: str
    state: GameState
    board: Board
    packets_queue: Queue
    current_tick: int
    timeout: int
    CONFIG: {}

    def __init__(self, uid: str = str(uuid.uuid4()), **kwargs):
        super(Game, self).__init__(daemon=True, name="Game_%s" % uid, **kwargs)
        self.channel_layer = get_channel_layer()
        self.uid = uid
        self.state = GameState.WAITING_PLAYERS
        self.packets_queue = Queue()
        self.current_tick = 0
        self.timeout = 0
        self.CONFIG = getattr(settings, "ENGINE_CONFIG", None)

    def run(self) -> None:
        # Starting game thread
        self.state = GameState.WAITING_PLAYERS

        # while state isnt stop thread
        while self.state is not GameState.STOP_THREAD:
            # game tick
            self.tick()

            # sleep x ticks per second
            time.sleep(1 / self.CONFIG.get('TICK_RATE'))

        # execute last func before stop
        self.proceed_stop()

    def tick(self):
        """
        Main function: every tick, this function will be executed
        """

        # Blocking queue
        self.packets_queue.join()

        # Process all packets in queue
        while not self.packets_queue.empty():
            self.process_packet(self.packets_queue.get(block=False))

        # Unblock
        self.packets_queue.task_done()

        # Do logic here

    def process_packet(self, packet: Packet):
        pass

    def proceed_stop(self):
        pass


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

    def send_packet(self, game_uid: str, packet: Packet):
        """
        Add packet to game packets queue
        Blocking thread until packet is added to queue
        :param game_uid: UUID of an existing game
        :param packet: Packet to send
        """
        if game_uid not in self.games:
            raise GameNotExistsException()

        # Blocking function that adds packet to queue
        self.games[game_uid].packets_queue.put(packet)
