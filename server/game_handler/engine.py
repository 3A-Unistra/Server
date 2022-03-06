import uuid
from enum import Enum
from threading import Thread
from queue import Queue
from channels.layers import get_channel_layer

from server.game_handler.data import Board

"""
States:
-> Démarrage -> démarrage timer remplacement joueur par un bot.
-> Attente de nb_joueurs AppletReady
-> Lorsque ce nombre est atteint => GameStart
-> On attends 2-3 secondes
-> On envoie un paquet GameStartDice

"""


class GameState(Enum):
    WAITING_PLAYERS = 0
    STARTING = 1
    START_DICE = 2


class Game:
    uid: str
    state: GameState
    board: Board
    queue: Queue

    def __init__(self, uid: str = str(uuid.uuid4())):
        self.channel_layer = get_channel_layer()
        self.uid = uid
        self.state = GameState.WAITING_PLAYERS


class Engine(Thread):
    games: [Game]

    def __init__(self, **kwargs):
        super(Engine, self).__init__(daemon=True, name="GameEngine", **kwargs)

    def add_game(self, game: Game):
        pass

    def remove_game(self, game: Game):
        pass
