import random
from typing import List, Optional

import names

from . import Player, Bank
from .auction import Auction
from .cards import ChanceCard, CommunityCard, CardActionType, Card
from django.conf import settings

from .exchange import Exchange
from .squares import Square, JailSquare, StationSquare, CompanySquare, \
    OwnableSquare, PropertySquare

from server.game_handler.models import User


class Board:
    squares: List[Square]
    community_deck: List[CommunityCard]
    chance_deck: List[ChanceCard]
    bank: Bank
    board_money: int
    players: List[Player]
    players_nb: int
    bots_nb: int
    bot_names: []
    current_player_index: int
    prison_square_index: int
    current_round: int
    remaining_round_players: int
    starting_balance: int
    current_exchange: Optional[Exchange]
    current_auction: Optional[Auction]

    # Options
    option_go_case_double_money: bool
    option_auction_enabled: bool
    option_password: str
    option_is_private: bool
    option_max_rounds: int  # > 0 => activated
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

    # Totals
    total_squares: int
    total_company_squares: int
    total_properties_color_squares: {}  # {'color': 'properties_same_color'}

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
        self.current_round = 0
        self.remaining_round_players = 0
        self.option_go_case_double_money = False
        self.option_auction_enabled = False
        self.option_password = ""
        self.option_is_private = False
        self.option_max_time = 0
        self.option_max_rounds = 0
        self.total_squares = 0
        self.total_company_squares = 0
        self.total_properties_color_squares = {}
        self.current_exchange = None
        self.current_auction = None
        self.bank = Bank(0, 0)  # TODO: AFTER AKI'S MERGE
        self.search_square_indexes()
        self.search_card_indexes()
        self.option_first_round_buy = False
        self.CONFIG = getattr(settings, "ENGINE_CONFIG", None)
        self.starting_balance = self.CONFIG.get("STARTING_BALANCE_DEFAULT")
        self.search_square_indexes()
        self.search_card_indexes()

    def load_data(self, squares: List[Square],
                  community_deck: List[CommunityCard],
                  chance_deck: List[ChanceCard]):
        self.squares = squares
        self.community_deck = community_deck
        self.chance_deck = chance_deck

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

    def set_option_max_rounds(self, nb_rounds):
        """
        this function set the max_nb_rounds option if the max_time is within
        the [min, max] (else, default value is used)
        :param nb_rounds: a number of rounds
        """
        if nb_rounds < self.CONFIG.get('NB_ROUNDS_MIN') or \
                nb_rounds > self.CONFIG.get('NB_ROUNDS_MAX'):
            self.option_max_rounds = self.CONFIG.get('NB_ROUNDS_DEFAULT')

        else:
            self.option_max_rounds = nb_rounds

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

    def assign_piece(self, user: User):
        """
        assigns a piece to a player
        If the favorite piece from the player is taken, it'll assign a random
        non-taken piece
        :param user: User
        """

        favorite_piece = user.piece
        player = self.get_player(user.id)

        taken = False
        for player in self.players:
            if player.piece == favorite_piece:
                taken = True
                break

        if not taken:
            player.piece = favorite_piece
            return favorite_piece

        if taken:
            taken_new_piece = False
            # iterating on all the pieces to get a free one
            for i in range(self.CONFIG.get('MAX_PIECE_NB')):
                taken_new_piece = False
                for player in self.players:
                    if player.piece == i:
                        taken_new_piece = True
                        break
                if not taken_new_piece:
                    player.piece = i
                    return i

        return -1   # this should not happen

    def search_square_indexes(self):
        """
        Search special square indexes
        """
        self.total_company_squares = 0
        self.total_squares = len(self.squares)
        self.total_properties_color_squares = {}

        for i in range(len(self.squares)):
            square = self.squares[i]
            if isinstance(square, JailSquare):
                self.prison_square_index = i
                continue

            if isinstance(square, CompanySquare):
                self.total_company_squares += 1
                continue

            if isinstance(square, PropertySquare):
                if square.color in self.total_properties_color_squares:
                    self.total_properties_color_squares[square.color] += 1
                else:
                    self.total_properties_color_squares[square.color] = 1

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

        # update remaining round players
        self.remaining_round_players -= 1

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
        return [player for player in self.players if not player.online]

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
        return [player for player in self.players if player.online]

    def get_online_real_players(self) -> List[Player]:
        """
        :return: Online players, bots excluded
        """
        return [player for player in self.players if
                (player.online and not player.bot)]

    def get_non_bankrupt_players(self) -> List[Player]:
        """
        :return: Non bankrupted players (bots included)
        """
        return [player for player in self.players if not player.bankrupt]

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
                           + cases) % self.total_squares
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
        return [a for a in self.squares if isinstance(a, OwnableSquare)]

    def get_property_squares(self) -> List[PropertySquare]:
        """
        :return: List of property squares
        """
        return [a for a in self.squares if isinstance(a, PropertySquare)]

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

    def compute_current_round(self) -> int:
        """
        Computes current round, (current_tour += 1) if all players have played.
        :return: Computed current round
        """
        if self.remaining_round_players == 0:
            self.remaining_round_players = len(self.get_non_bankrupt_players())
            self.current_round += 1
        return self.current_round

    def get_owned_squares(self, player: Player) -> List[OwnableSquare]:
        """
        List of owned squares by player
        :param player: Owner
        :return: List of owned squares
        """
        return [square for square in self.squares if
                isinstance(square, OwnableSquare)
                and square.owner == player]

    def get_rent(self, case: OwnableSquare, dices: (int, int) = (0, 0)) -> int:
        """
        get rent of case.
        - StationSquare: count how many stations the player have
        - CompanySquare: roll dices? or last dices?
        - PropertySquare: if houses==0, check if all properties with same color
                        if houses > 0, calculate rent
        :param case: Case where a player should pay a rent
        :param dices: Company squares need last dices of player
        :return: Computed rent
        """
        owned_squares = self.get_owned_squares(player=case.owner)

        if isinstance(case, StationSquare):
            stations_count = len(
                [a for a in owned_squares if
                 isinstance(a, StationSquare) and not a.mortgaged])
            # 0 stations => 0
            # 1 station: x1 ; 2 stations: x2 ; 3 stations: x4 ; 4 stations: x8
            return 0 if stations_count == 0 else 2 ** (
                    stations_count - 1) * case.get_rent()
        elif isinstance(case, CompanySquare):
            company_count = len(
                [a for a in owned_squares if
                 isinstance(a, CompanySquare) and not a.mortgaged])
            # if player has all companies, dices are multiplied by 10
            # else dices are multiplied by 4
            multiplier = 10 if company_count == self.total_company_squares \
                else 4
            return multiplier * sum(dices)
        elif isinstance(case, PropertySquare) and case.nb_house == 0:
            # Count all properties owned by the player and which have the same
            # color
            if self.has_property_group(color=case.color,
                                       owned_squares=owned_squares):
                # If player has all properties of group, multiply rent by 2
                return case.get_rent() * 2

        return case.get_rent()

    def get_property(self, property_id: int) -> Optional[OwnableSquare]:
        """
        Get a property square instance by id
        :param property_id: ID of property sqaure
        :return: Property square by id,
                None if id is not found or square is not ownable
        """
        if property_id < 0 or property_id >= self.total_squares:
            return None

        found = self.squares[property_id]

        return found if isinstance(found, OwnableSquare) else None

    def has_property_group(self, color: str,
                           player: Optional[Player] = None,
                           owned_squares: List[OwnableSquare] = None) -> bool:
        """
        If player has the whole group or not
        :param color: Group color
        :param player: Owner, optional, only if owned_squares is None
        :param owned_squares: Players owned squares
               (if none, self.get_owned_squares(player) is called)
        :return: If player has whole property group or not
        """

        if owned_squares is None:
            if player is None:
                return False
            owned_squares = self.get_owned_squares(player)

        property_count = len([a for a in owned_squares
                              if isinstance(a, PropertySquare)
                              and a.color == color])

        return property_count == self.total_properties_color_squares[color]

    def get_house_count_by_owned_group(self, color: str,
                                       player: Optional[Player] = None,
                                       owned_squares: List[
                                           OwnableSquare] = None) -> int:
        """
        Get houses by owned properties in a group
        :param color: Group color
        :param player: Owner, optional, only if owned_squares is None
        :param owned_squares: Players owned squares
               (if none, self.get_owned_squares(player) is called)
        :return: Total houses from the properties of a group
                (-1 if owned_squares and player are None)
        """
        if owned_squares is None:
            if player is None:
                return -1
            owned_squares = self.get_owned_squares(player)

        return sum([a.nb_house for a in owned_squares if
                    isinstance(a, PropertySquare) and a.color == color])

    def get_group_property_squares(self, color: str,
                                   player: Optional[Player] = None,
                                   owned_squares: List[OwnableSquare]
                                   = None) -> List[PropertySquare]:
        """
        Get properties of a group owned by a player
        :param color: Group color
        :param player: Owner, optional, only if owned_squares is None
        :param owned_squares: Players owned squares
               (if none, self.get_owned_squares(player) is called)
        :raises InsufficientGroupException when player not own all properties
                of the group
        :return: Properties of a group ([] if owned_squares & player are None)
        """
        if owned_squares is None:
            if player is None:
                return []
            owned_squares = self.get_owned_squares(player)

        return [a for a in owned_squares if
                isinstance(a, PropertySquare) and a.color == color]
