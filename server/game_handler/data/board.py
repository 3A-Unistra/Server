import random
from typing import List, Optional

import names

from . import Player
from .cards import ChanceCard, CommunityCard, CardActionType, Card
from django.conf import settings
from .squares import Square, JailSquare, StationSquare, CompanySquare, \
    OwnableSquare, PropertySquare

from server.game_handler.models import User


class Board:
    squares: List[Square]
    community_deck: List[CommunityCard]
    chance_deck: List[ChanceCard]
    board_money: int
    players: List[Player]
    players_nb: int
    bots_nb: int
    bot_names: []
    current_player_index: int
    prison_square_index: int
    round: int
    starting_balance: int

    # Options
    option_go_case_double_money: bool
    option_auction_enabled: bool
    option_password: str
    option_is_private: bool
    option_maxnb_rounds: int
    option_max_time: int  # max time per rounds
    option_first_round_buy: bool

    CONFIG = {}

    # Card indexes
    community_card_indexes = {
        'leave_jail': -1
    }
    chance_card_indexes = {
        'leave_jail': -1
    }

    def __init__(self, squares=None):
        self.squares = [] if squares is None else squares
        self.community_deck = []
        self.chance_deck = []
        self.board_money = 0
        self.players = []
        self.players_nb = 0
        self.bots_nb = 0
        self.current_player_index = 0
        self.prison_square_index = -1
        self.bot_names: []
        self.round = 0
        self.option_go_case_double_money = False
        self.option_auction_enabled = False
        self.option_password = ""
        self.option_is_private = False
        self.starting_balance = getattr(settings, "MONEY_START_DEFAULT", 1000)
        self.option_maxnb_rounds = 0
        self.option_max_time = 0
        self.option_first_round_buy = False
        self.CONFIG = getattr(settings, "ENGINE_CONFIG", None)
        self.search_square_indexes()
        self.search_card_indexes()

    def set_option_max_time(self, given_time):
        """
        this function set the max_time option if the max_time is within the
        [min, max] (else, default value is used
        :param given_time: a time
        """
        if given_time < self.CONFIG.get('TIME_ROUNDS_MIN') or \
                given_time > self.CONFIG.get('TIME_ROUNDS_MAX'):
            self.option_max_time = self.CONFIG.get('TIME_ROUNDS_DEFAULT')

        else:
            self.option_max_time = given_time

    def set_option_maxnb_rounds(self, nb_rounds):
        """
        this function set the max_nb_rounds option if the max_time is within
        the [min, max] (else, default value is used)
        :param nb_rounds: a number of rounds
        """
        if nb_rounds < self.CONFIG.get('NB_ROUNDS_MIN') or \
                nb_rounds > self.CONFIG.get('NB_ROUNDS_MAX'):
            self.option_maxnb_rounds = self.CONFIG.get('NB_ROUNDS_DEFAULT')

        else:
            self.option_maxnb_rounds = nb_rounds

    def set_option_start_balance(self, balance):
        """
        this function set the max_nb_rounds option if the max_time is within
        the [min, max] (else, default value is used)
        :param balance: balance
        """
        if balance < self.CONFIG.get('MONEY_START_MIN') or \
                balance > self.CONFIG.get('MONEY_START_MAX'):
            self.starting_balance = self.CONFIG.get('MONEY_START_DEFAULT')

        else:
            self.starting_balance = balance

    def assign_piece(self, player_token: str):
        """
        assigns a piece to a player
        If the favorite piece from the player is taken, it'll assign a random
        non-taken piece
        :param player_token: player id
        """

        try:  # get user from database
            user = User.objects.get(id=player_token)
        except User.DoesNotExist:
            return

        favorite_piece = user.piece
        taken = False
        for player in self.players:
            if player.piece == favorite_piece:
                taken = True
                break

        if taken:
            # iterating on all the pieces to get a free one
            for i in range(self.CONFIG.get('MAX_PIECE_NB')):
                taken_new_piece = False
                for player in self.players:
                    if player.piece == i:
                        taken_new_piece = True
                        break
                if not taken_new_piece:
                    self.get_player(player_token).piece = i
                    return i

        else:
            self.get_player(player_token).piece = favorite_piece
            return favorite_piece

    def search_square_indexes(self):
        """
        Search special square indexes
        """
        for i in range(len(self.squares)):
            square = self.squares[i]
            if isinstance(square, JailSquare):
                self.prison_square_index = i
                break

    def search_card_indexes(self):
        """
        Search special card indexes (leave_jail)
        Writes in <chance or community>_card_indexes
        """
        for i in range(len(self.chance_deck)):
            card = self.chance_deck[i]
            if card.action_type == CardActionType.LEAVE_JAIL:
                self.chance_card_indexes['leave_jail'] = i
                break
        for i in range(len(self.community_deck)):
            card = self.community_deck[i]
            if card.action_type == CardActionType.LEAVE_JAIL:
                self.community_card_indexes['leave_jail'] = i
                break

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
        for i in range(len(self.players)):
            if self.players[i] == player:
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
            if player.get_id() == uid:
                return player
        return None

    def player_exists(self, uid: str) -> bool:
        return self.get_player(uid) is not None

    def add_player(self, player: Player):
        if self.player_exists(player.get_id()):
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

    def get_online_real_players(self) -> List[Player]:
        """
        :return: Online players, bots excluded
        """
        players = []
        for player in self.players:
            if player.online is True and player.bot is False:
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
            if comp == player:
                continue

            if comp.dices_value() == player.dices_value():
                return None

        return player

    # Cases processing here

    def move_player_with_dices(self, player: Player) -> bool:
        """
        :param player: Player to move
        :return: If player reached "0" (start) case
        """
        return self.move_player(player=player, cases=player.dices_value())

    def move_player(self, player: Player, cases: int) -> bool:
        """
        :param player: Player to move
        :param cases: Cases to move
        :return: If player reached "0" (start) case
        """
        temp_position = player.position
        player.position = (player.position
                           + cases) % len(self.squares)
        return player.position < temp_position

    def draw_random_card(self, deck: List[Card]) -> Optional[Card]:
        available_deck = [card for card in deck if card.available]

        if len(available_deck) == 0:
            return None

        return random.choice(available_deck)

    def draw_random_chance_card(self) -> Optional[ChanceCard]:
        """
        :return: Randomly drawn chance card, (+ jail card if available)
                Could be None if no card was found or available
        """
        return self.draw_random_card(self.chance_deck)

    def draw_random_community_card(self) -> Optional[CommunityCard]:
        """
        :return: Randomly drawn community card, (+ jail card if available)
                Could be None if no card was found or available
        """
        return self.draw_random_card(self.community_deck)

    def use_chance_jail_card(self, player: Player):
        player.jail_cards['chance'] = False
        self.chance_deck[
            self.chance_card_indexes['leave_jail']].available = True

    def use_community_jail_card(self, player: Player):
        player.jail_cards['community'] = False
        self.community_deck[
            self.community_card_indexes['leave_jail']].available = True

    def retarget_player_bank_debts(self, new_target: Player):
        """
        change all debts targeting the bank (None) to this player (new_target)
        :param new_target: Target
        """
        for player in self.players:
            for debt in player.debts:
                if debt.creditor is not None:
                    continue
                debt.creditor = new_target

    def find_closest_station_index(self, player: Player) -> int:
        """
        :param player: Player (get player position)
        :return: Index of closest station, or -1 if not found
        """
        position = player.position
        squares_len = len(self.squares)

        for i in range(squares_len):
            position = (position + 1) % squares_len

            if isinstance(self.squares[position], StationSquare):
                return position

        return -1

    def find_closest_company_index(self, player: Player) -> int:
        """
        :param player: Player (get player position)
        :return: Index of closest company, or -1 if not found
        """
        position = player.position
        squares_len = len(self.squares)

        for i in range(squares_len):
            position = (position + 1) % squares_len

            if isinstance(self.squares[position], CompanySquare):
                return position

        return -1

    def get_ownable_squares(self) -> List[OwnableSquare]:
        """
        :return: List of ownable squares
        """
        result = []
        for square in self.squares:
            if isinstance(square, OwnableSquare):
                result.append(result)
        return result

    def get_property_squares(self) -> List[PropertySquare]:
        """
        :return: List of property squares
        """
        result = []
        for square in self.squares:
            if isinstance(square, PropertySquare):
                result.append(square)
        return result

    def get_player_buildings_count(self, player: Player) -> (int, int):
        """
        Get total houses and hotels count
        :param player: Player (owner)
        :return: (houses, hotels) Total houses and hotels count
        """
        houses = 0
        hotels = 0

        for square in self.get_property_squares():
            if square.owner != player:
                continue

            if square.has_hotel():
                hotels += 1
            else:
                houses += square.nb_house

        return houses, hotels
