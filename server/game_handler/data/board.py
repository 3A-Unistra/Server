from typing import List

from . import Card, Player
from .squares import Square


class Board:
    board: List[Square]
    community_deck: List[Card]
    chance_deck: List[Card]
    prison_square: int
    board_money: int
    players: [Player]
    players_nb: int
    bots_nb: int

    def __init__(self):
        self.board = []
        self.community_deck = []
        self.chance_deck = []
        self.prison_square = 0
        self.board_money = 0
        self.players = []
        self.players_nb = 0
        self.bots_nb = 0

    def get_player(self, uid: str):
        for player in self.players:
            if player.id_ == uid:
                return player
        return None

    def player_exists(self, uid: str):
        return self.get_player(uid) is not None

    def add_player(self, player: Player):
        if self.player_exists(player.id_):
            return

        self.players.append(player)

    def get_online_players_count(self):
        """
        Counts online players, bot are included too
        """
        return sum(1 for player in self.players if player.online)
