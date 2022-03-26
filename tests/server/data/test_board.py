from unittest import TestCase

from server.game_handler.data import Player, Board
from server.game_handler.data.cards import CommunityCard, CardActionType, \
    ChanceCard, Card
from server.game_handler.engine import Engine
from server.game_handler.models import User


def create_players() -> (Player, Player, Player):
    player1 = Player(bot=False,
                     user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
    player2 = Player(bot=False,
                     user=User(id="153e1f5e-3411-32c5-9bc5-037358c47100"))
    player3 = Player(bot=False,
                     user=User(id="413e1f2e-3411-32c5-9bc5-037358c47120"))
    return player1, player2, player3


class TestPacket(TestCase):
    engine: Engine()

    def setUp(self):
        self.engine = Engine()

    def create_board(self) -> Board:
        board = Board()
        board.chance_deck = self.engine.chance_deck.copy()
        board.community_deck = self.engine.community_deck.copy()
        board.squares = self.engine.squares.copy()
        return board

    def test_search_card_indexes(self):
        board = self.create_board()
        board.search_card_indexes()
        assert 'leave_jail' in board.chance_card_indexes
        assert board.chance_card_indexes['leave_jail'] != -1

    def test_search_square_indexes(self):
        board = self.create_board()
        board.search_square_indexes()
        assert board.prison_square_index != -1

    def test_board_add_player(self):
        board = self.create_board()
        player = Player()
        board.add_player(player)
        assert len(board.players) == 1

        # test not add duplicates
        board.add_player(player)
        assert len(board.players) == 1

    def test_board_players_offline(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)
        assert len(board.players) == 3
        player1.connect()
        assert len(board.get_offline_players()) == 2
        player2.connect()
        assert len(board.get_offline_players()) == 1

    def test_board_player_exists(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        board.add_player(player1)
        assert board.player_exists(player1.get_id())

    def test_board_players_online(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)
        assert len(board.players) == 3
        player1.connect()
        assert len(board.get_online_players()) == 1
        player2.connect()
        assert len(board.get_online_players()) == 2

        assert board.get_online_players()[0] == player1
        assert board.get_online_players()[1] == player2

    def test_get_online_players_count(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)

        assert board.get_online_players_count() == 0

        player1.connect()
        assert board.get_online_players_count() == 1

        player2.connect()
        assert board.get_online_players_count() == 2

        player3.connect()
        assert board.get_online_players_count() == 3

    def test_get_non_bankrupt_players(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)

        assert len(board.get_non_bankrupt_players()) == 3

        player1.bankrupt = True
        assert len(board.get_non_bankrupt_players()) == 2

        player2.bankrupt = True
        assert len(board.get_non_bankrupt_players()) == 1

    def test_get_online_real_players_count(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)

        # Bot bot
        player3.bot = True
        player3.online = True

        assert board.get_online_real_players_count() == 0

        player1.connect()
        assert board.get_online_real_players_count() == 1

        player2.connect()
        assert board.get_online_real_players_count() == 2

    def test_board_next_player(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)
        board.players_nb = 3
        assert board.get_current_player().get_id() == player1.get_id()
        assert board.next_player().get_id() == player2.get_id()
        assert board.next_player().get_id() == player3.get_id()
        assert board.next_player().get_id() == player1.get_id()
        player2.bankrupt = True
        assert board.next_player().get_id() == player3.get_id()
        player3.bankrupt = True
        assert board.next_player().get_id() == player1.get_id()
        assert board.next_player().get_id() == player1.get_id()

    def test_board_get_highest_dice(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)
        player1.connect()
        player2.connect()
        player3.connect()

        assert len(board.get_online_players()) == 3
        player1.current_dices = (1, 1)
        player2.current_dices = (2, 1)
        player3.current_dices = (2, 3)

        highest = board.get_highest_dice()
        assert highest is not None
        assert highest.get_id() == player3.get_id()

        # Test same dice score
        player2.current_dices = (2, 3)

        assert board.get_highest_dice() is None

    def test_board_use_community_jail_card(self):
        board = self.create_board()
        board.search_card_indexes()
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        board.add_player(player1)

        board.use_community_jail_card(player1)

        assert player1.jail_cards['community'] is False
        assert board.community_deck[
            board.community_card_indexes['leave_jail']].available

    def test_board_use_chance_jail_card(self):
        board = self.create_board()
        board.search_card_indexes()
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        board.add_player(player1)

        board.use_chance_jail_card(player1)

        assert player1.jail_cards['chance'] is False
        assert board.chance_deck[
            board.chance_card_indexes['leave_jail']].available

        board.remove_player(player1)

    def test_draw_random_community_card(self):
        board = self.create_board()
        card = board.draw_random_community_card()
        assert card is not None
        assert isinstance(card, CommunityCard)

    def test_draw_random_chance_card(self):
        board = self.create_board()
        card = board.draw_random_chance_card()
        assert card is not None
        assert isinstance(card, ChanceCard)

    def test_draw_random_card(self):
        board = self.create_board()
        card_deck = [Card(
            id_=1,
            action_type=CardActionType.LEAVE_JAIL,
            action_value=0
        ), Card(
            id_=2,
            action_type=CardActionType.GIVE_ALL,
            action_value=20
        )]

        card_deck[0].available = False
        card_deck[1].available = False

        assert len(card_deck) == 2

        card = board.draw_random_card(card_deck)

        # Two cards are not available, card should be none
        assert card is None

        card_deck[0].available = True

        card = board.draw_random_card(card_deck)
        assert card.id_ == 1

        card_deck[0].available = False
        card_deck[1].available = True

        card = board.draw_random_card(card_deck)
        assert card.id_ == 2

    def test_retarget_player_bank_debts(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)

        player2.add_debt(creditor=None, amount=500)
        player2.add_debt(creditor=None, amount=50)
        player3.add_debt(creditor=None, amount=100)
        player3.add_debt(creditor=player2, amount=100)

        board.retarget_player_bank_debts(player1)

        assert player2.debts[0].creditor == player1
        assert player2.debts[1].creditor == player1
        assert player3.debts[0].creditor == player1

    def test_find_closest_company_index(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))

        player1.position = 2
        assert board.find_closest_company_index(player1) == 12

        player1.position = 13
        assert board.find_closest_company_index(player1) == 28

        player1.position = 29
        assert board.find_closest_company_index(player1) == 12

        board.squares = []
        assert board.find_closest_company_index(player1) == -1

    def test_find_closest_station_index(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))

        player1.position = 2
        assert board.find_closest_station_index(player1) == 5

        player1.position = 13
        assert board.find_closest_station_index(player1) == 15

        player1.position = 18
        assert board.find_closest_station_index(player1) == 25

        player1.position = 27
        assert board.find_closest_station_index(player1) == 35

        player1.position = 37
        assert board.find_closest_station_index(player1) == 5

        board.squares = []
        assert board.find_closest_station_index(player1) == -1

    def test_get_player_idx(self):
        board = self.create_board()
        player1, player2, player3 = create_players()
        player4 = Player(bot=False,
                         user=User(id="283e3f3e-3411-44c5-9bc5-037358c47100"))

        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)

        assert board.get_player_idx(player1) == 0
        assert board.get_player_idx(player2) == 1
        assert board.get_player_idx(player3) == 2
        assert board.get_player_idx(player4) == -1

    def test_get_ownable_squares(self):
        board = self.create_board()
        assert len(board.get_ownable_squares()) == 28

    def test_get_property_squares(self):
        board = self.create_board()
        assert len(board.get_property_squares()) == 22

    def test_get_player_buildings_count(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e3f3e-3411-44c5-9bc5-037358c47100"))

        houses, hotels = board.get_player_buildings_count(player1)
        assert houses == 0
        assert hotels == 0

        # set owner
        for i in range(3):
            board.get_property_squares()[i].owner = player1

        board.get_property_squares()[0].nb_house += 5

        houses, hotels = board.get_player_buildings_count(player1)
        assert houses == 0
        assert hotels == 1

        board.get_property_squares()[0].nb_house += 5
        board.get_property_squares()[1].nb_house += 2
        board.get_property_squares()[2].nb_house += 1

        houses, hotels = board.get_player_buildings_count(player1)
        assert houses == 3
        assert hotels == 1

    def test_move_player(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e3f3e-3411-44c5-9bc5-037358c47100"))

        assert player1.position == 0

        assert not board.move_player(player1, 3)
        assert player1.position == 3

        # set player to last case
        player1.position = len(board.squares) - 1

        assert board.move_player(player1, 3)
        assert player1.position == 2

    def test_move_player_with_dices(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e3f3e-3411-44c5-9bc5-037358c47100"))

        assert player1.position == 0
        player1.current_dices = (3, 3)

        assert not board.move_player_with_dices(player1)
        assert player1.position == 6

        # set player to last case
        player1.position = len(board.squares) - 1
        player1.current_dices = (3, 3)

        assert board.move_player_with_dices(player1)
        assert player1.position == 5

    def test_get_online_real_players(self):
        board = self.create_board()
        player1, player2, player3 = create_players()

        board.add_player(player1)
        board.add_player(player2)
        board.add_player(player3)

        player1.connect()
        player2.connect()

        assert len(board.get_online_real_players()) == 2

        player3.connect()

        assert len(board.get_online_real_players()) == 3

    def test_set_bot_names(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e3f3e-3411-44c5-9bc5-037358c47100"))

        board.add_player(player1)
        board.set_bot_names()

        assert player1.bot_name is not None
        assert player1.bot_name != ""

    def test_get_random_bot_name(self):
        board = self.create_board()
        bot_name = board.get_random_bot_name()

        assert bot_name is not None
        assert bot_name != ""
        assert bot_name.startswith("Bot")

    def test_bot_name_used(self):
        board = self.create_board()
        player1 = Player(bot=False,
                         user=User(id="283e3f3e-3411-44c5-9bc5-037358c47100"))
        board.add_player(player1)
        player1.bot_name = "bot_name"

        assert board.bot_name_used("bot_name")
        assert not board.bot_name_used("bot_prout")

    def test_set_current_player(self):
        board = self.create_board()
        player1, player2, player3 = create_players()

        board.add_player(player1)
        board.add_player(player2)

        assert board.set_current_player(player3) == -1
        assert board.set_current_player(player2) == 1
        assert board.current_player_index == 1
