from unittest import TestCase

from server.game_handler.data import Player, Board
from server.game_handler.data.cards import CommunityCard, CardActionType, \
    ChanceCard, Card
from server.game_handler.models import User


class TestPacket(TestCase):
    board: Board

    def setUp(self):
        self.board = Board()

    def test_board_add_player(self):
        player = Player()
        self.board.add_player(player)
        assert len(self.board.players) == 1
        self.board.remove_player(player)

    def test_board_players_offline(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="153e1f5e-3411-32c5-9bc5-037358c47100"))
        player3 = Player(bot=False,
                         user=User(id="413e1f2e-3411-32c5-9bc5-037358c47120"))
        self.board.add_player(player1)
        self.board.add_player(player2)
        self.board.add_player(player3)
        assert len(self.board.players) == 3
        player1.connect()
        assert len(self.board.get_offline_players()) == 2
        player2.connect()
        assert len(self.board.get_offline_players()) == 1
        self.board.remove_player(player1)
        self.board.remove_player(player2)
        self.board.remove_player(player3)

    def test_board_player_exists(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        self.board.add_player(player1)
        assert self.board.player_exists(player1.get_id())
        self.board.remove_player(player1)

    def test_board_players_online(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="153e1f5e-3411-32c5-9bc5-037358c47100"))
        player3 = Player(bot=False,
                         user=User(id="413e1f2e-3411-32c5-9bc5-037358c47120"))
        self.board.add_player(player1)
        self.board.add_player(player2)
        self.board.add_player(player3)
        assert len(self.board.players) == 3
        player1.connect()
        assert len(self.board.get_online_players()) == 1
        player2.connect()
        assert len(self.board.get_online_players()) == 2
        self.board.remove_player(player1)
        self.board.remove_player(player2)
        self.board.remove_player(player3)

    def test_board_next_player(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="153e1f5e-3411-32c5-9bc5-037358c47100"))
        player3 = Player(bot=False,
                         user=User(id="413e1f2e-3411-32c5-9bc5-037358c47120"))
        self.board.add_player(player1)
        self.board.add_player(player2)
        self.board.add_player(player3)
        self.board.players_nb = 3
        assert self.board.get_current_player().get_id() == player1.get_id()
        assert self.board.next_player().get_id() == player2.get_id()
        assert self.board.next_player().get_id() == player3.get_id()
        assert self.board.next_player().get_id() == player1.get_id()
        player2.bankrupt = True
        assert self.board.next_player().get_id() == player3.get_id()
        player3.bankrupt = True
        assert self.board.next_player().get_id() == player1.get_id()
        assert self.board.next_player().get_id() == player1.get_id()
        self.board.current_player_index = 0
        self.board.players_nb = 0
        self.board.remove_player(player1)
        self.board.remove_player(player2)
        self.board.remove_player(player3)

    def test_board_get_highest_dice(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="153e1f5e-3411-32c5-9bc5-037358c47100"))
        player3 = Player(bot=False,
                         user=User(id="413e1f2e-3411-32c5-9bc5-037358c47120"))
        self.board.add_player(player1)
        self.board.add_player(player2)
        self.board.add_player(player3)
        player1.connect()
        player2.connect()
        player3.connect()

        assert len(self.board.get_online_players()) == 3
        player1.current_dices = (1, 1)
        player2.current_dices = (2, 1)
        player3.current_dices = (2, 3)

        highest = self.board.get_highest_dice()
        assert highest is not None
        assert highest.get_id() == player3.get_id()

        # Test same dice score
        player2.current_dices = (2, 3)

        assert self.board.get_highest_dice() is None

        self.board.remove_player(player1)
        self.board.remove_player(player2)
        self.board.remove_player(player3)

    def test_board_use_community_jail_card(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        self.board.add_player(player1)

        self.board.community_deck.append(CommunityCard(
            id_=1,
            action_type=CardActionType.LEAVE_JAIL,
            action_value=0
        ))

        self.board.community_card_indexes['leave_jail'] = 0

        self.board.use_community_jail_card(player1)

        assert player1.jail_cards['community'] is False
        assert self.board.community_deck[0].available

        self.board.community_deck = []
        self.board.community_card_indexes = []
        self.board.remove_player(player1)

    def test_board_use_chance_jail_card(self):
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        self.board.add_player(player1)

        self.board.chance_deck.append(ChanceCard(
            id_=1,
            action_type=CardActionType.LEAVE_JAIL,
            action_value=0
        ))

        self.board.chance_card_indexes['leave_jail'] = 0

        self.board.use_chance_jail_card(player1)

        assert player1.jail_cards['chance'] is False
        assert self.board.chance_deck[0].available

        self.board.chance_deck = []
        self.board.chance_card_indexes = []
        self.board.remove_player(player1)

    def test_draw_random_community_card(self):
        self.board.community_deck.append(CommunityCard(
            id_=1,
            action_type=CardActionType.LEAVE_JAIL,
            action_value=0
        ))

        self.board.community_deck.append(CommunityCard(
            id_=2,
            action_type=CardActionType.GIVE_ALL,
            action_value=20
        ))

        assert len(self.board.community_deck) == 2

        card = self.board.draw_random_community_card()
        assert card.id_ == 1 or card.id_ == 2

        self.board.community_deck = []

    def test_draw_random_chance_card(self):
        self.board.chance_deck.append(ChanceCard(
            id_=1,
            action_type=CardActionType.LEAVE_JAIL,
            action_value=0
        ))

        self.board.chance_deck.append(ChanceCard(
            id_=2,
            action_type=CardActionType.GIVE_ALL,
            action_value=20
        ))

        assert len(self.board.chance_deck) == 2

        card = self.board.draw_random_chance_card()
        assert card.id_ == 1 or card.id_ == 2

        self.board.chance_deck = []

    def test_draw_random_card(self):
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

        card = self.board.draw_random_card(card_deck)

        # Two cards are not available, card should be none
        assert card is None

        card_deck[0].available = True

        card = self.board.draw_random_card(card_deck)
        assert card.id_ == 1

        card_deck[0].available = False
        card_deck[1].available = True

        card = self.board.draw_random_card(card_deck)
        assert card.id_ == 2
