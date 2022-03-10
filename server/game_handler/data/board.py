import random
from typing import List, Optional

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
    bot_names: []

    def __init__(self):
        self.board = []
        self.community_deck = []
        self.chance_deck = []
        self.prison_square = 0
        self.board_money = 0
        self.players = []
        self.players_nb = 0
        self.bots_nb = 0
        self.bot_names: []

    def get_player(self, uid: str) -> Optional[Player]:
        for player in self.players:
            if player.id_ == uid:
                return player
        return None

    def player_exists(self, uid: str) -> bool:
        return self.get_player(uid) is not None

    def add_player(self, player: Player):
        if self.player_exists(player.id_):
            return

        self.players.append(player)

    def get_online_players_count(self) -> int:
        """
        Counts online players, bots are included
        """
        return sum(1 for player in self.players if player.online)

    def get_online_real_players_count(self) -> int:
        """
        Counts online players, bots are excluded
        """
        return sum(1 for player in self.players if (
                player.online and not player.bot))

    def get_offline_players(self) -> []:
        """
        :return: Offline players (bots that are not connected)
        """
        offline = []
        for player in self.players:
            if player.online is False:
                offline.append(player)
        return offline

    def bot_name_used(self, name: str) -> bool:
        for player in self.players:
            if player.bot_name == name:
                return True
        return False

    def get_random_bot_name(self) -> str:
        """
        :return: Random bot name not
        """
        name: str = 'Bot'
        names_count = len(self.bot_names)
        i = names_count

        while i > 0:
            name = self.bot_names[random.randint(0, names_count)]
            if self.bot_name_used(name) is False:
                break
            i -= 1

        return '%s #%s' % (name, str(random.randint(1, 9)))

    def set_bot_names(self):
        """
        Set a bot name to all players
        """
        for player in self.players:
            player.bot_name = self.get_random_bot_name()

    def get_online_players(self):
        """
        :return: Online players, bots included
        """
        players = []
        for player in self.players:
            if player.online is True:
                players.append(player)
        return players
