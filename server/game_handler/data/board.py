import random
from typing import List, Optional

import names

from . import Card, Player
from .squares import Square


class Board:
    board: List[Square]
    community_deck: List[Card]
    chance_deck: List[Card]
    prison_square: int
    board_money: int
    players: List[Player]
    players_nb: int
    bots_nb: int
    bot_names: []
    current_player_index: int
    round: int

    def __init__(self):
        self.board = []
        self.community_deck = []
        self.chance_deck = []
        self.prison_square = 0
        self.board_money = 0
        self.players = []
        self.players_nb = 0
        self.bots_nb = 0
        self.current_player_index = 0
        self.bot_names: []
        self.round = 0

    def next_player(self) -> Player:
        """
        Setting next player (if player is bankrupt, goto next)
        :return: Next player playing
        """
        i = 0
        curr_idx = self.current_player_index

        while i < self.players_nb:
            curr_idx = (curr_idx + 1) % self.players_nb

            if not self.players[curr_idx].bankrupt:
                self.current_player_index = curr_idx
                break

            i += 1

        return self.players[self.current_player_index]

    def get_player_idx(self, player: Player) -> int:
        for i in range(0, self.players_nb):
            if self.players[i].public_id == player.public_id:
                return i
        return -1

    def set_current_player(self, player: Player) -> int:
        """
        Set current playing player
        :param player: Player
        :return: -1 if player not found, idx if found
        """
        idx = self.get_player_idx(player)
        if idx == -1:
            return -1
        self.current_player_index = idx
        return idx

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def get_player(self, uid: str) -> Optional[Player]:
        for player in self.players:
            if player.public_id == uid:
                return player
        return None

    def player_exists(self, uid: str) -> bool:
        return self.get_player(uid) is not None

    def add_player(self, player: Player):
        if self.player_exists(player.public_id):
            return

        self.players.append(player)

    def remove_player(self, player: Player):
        self.players.remove(player)

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

    def get_offline_players(self) -> List[Player]:
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
        i = 50  # Max 50 tries
        while i > 0:
            name = names.get_first_name()
            if self.bot_name_used(name) is False:
                return 'Bot %s' % name
            i -= 1
        # If above code fails, then we generate a name like: Bot #<random>
        return 'Bot #%d' % random.randint(1, 9)

    def set_bot_names(self):
        """
        Set a bot name to all players
        """
        for player in self.players:
            player.bot_name = self.get_random_bot_name()

    def get_online_players(self) -> List[Player]:
        """
        :return: Online players, bots included
        """
        players = []
        for player in self.players:
            if player.online is True:
                players.append(player)
        return players

    def get_highest_dice(self) -> Optional[Player]:
        """
        Returns the highest dice score player in game
        If two players have the same dice score, then None is returned
        """
        players = self.get_online_players()
        player: Player = players.pop(0)

        for comp in players:
            if comp.dices_value() > player.dices_value():
                player = comp

        # Check for uniqueness
        for comp in self.get_online_players():
            if comp.public_id is player.public_id:
                continue

            if comp.dices_value() == player.dices_value():
                return None

        return player
