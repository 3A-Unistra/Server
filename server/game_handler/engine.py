from enum import Enum

from channels.layers import get_channel_layer

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

    def __init__(self):
        self.channel_layer = get_channel_layer()
