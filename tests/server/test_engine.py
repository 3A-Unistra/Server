import json
import os
from unittest import TestCase

from django.conf import settings

from server.game_handler.data import Player, Card
from server.game_handler.data.cards import CardActionType, ChanceCard, \
    CommunityCard
from server.game_handler.data.packets import Packet
from server.game_handler.engine import Engine, Game, GameState

# overwrite broadcast_packet method
from server.game_handler.models import User


def new_broadcast_packet(self, packet: Packet):
    pass


def game_instance_overwrited() -> Game:
    game = Game()
    # overwrite broadcast packet
    game.broadcast_packet = new_broadcast_packet.__get__(game, Game)

    return game


class TestPacket(TestCase):
    engine: Engine

    def setUp(self):
        self.engine = Engine()

    def test_add_game(self):
        game = Game()
        self.engine.add_game(game)

        assert len(self.engine.games) == 1
        assert game.board.prison_square_index == 10
        assert game.board.chance_card_indexes['leave_jail'] == 15
        assert game.board.community_card_indexes['leave_jail'] == 15
        assert game.state == GameState.LOBBY

        game.proceed_stop()

        assert len(self.engine.games) == 0
        assert game.state == GameState.STOP_THREAD

    def test_player_balance_update(self):
        game = game_instance_overwrited()
        player = Player()
        game.player_balance_update(player=player,
                                   new_balance=50,
                                   reason="test")
        assert player.money == 50

    def test_player_balance_pay(self):
        game = game_instance_overwrited()
        player1 = Player(bot=False,
                         user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="223e1f5e-3411-44c5-9bc5-037358c47100"))
        player3 = Player(bot=False,
                         user=User(id="212e1f5e-3411-44c5-9bc5-037358c47100"))

        game.board.add_player(player1)
        game.board.add_player(player2)
        game.board.add_player(player3)

        # test player1 pay 50 to player2 but has 0
        game.player_balance_pay(player=player1,
                                receiver=player2,
                                amount=50,
                                reason="test")

        assert player1.money == 0
        assert player2.money == 0
        assert player1.has_debts()
        assert player1.debts[0].amount == 50
        assert player1.debts[0].creditor == player2
        assert not player2.has_debts()

        # test player1 receive 50
        game.player_balance_receive(player=player1,
                                    amount=50,
                                    reason="test")
        assert player1.money == 0
        assert player2.money == 50
        assert not player1.has_debts()
        assert not player2.has_debts()

        # test recursive method
        # Player 1 -> debt 50 Player2
        # Player 2 -> debt 50 Player3
        # Player 3 -> debt 30 Player1 -> debt 30 Player2

    def test_player_balance_receive(self):
        game = game_instance_overwrited()
        player1 = Player(bot=False,
                         user=User(id="183e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="523e1f5e-3411-44c5-9bc5-037358c47100"))
        player3 = Player(bot=False,
                         user=User(id="612e1f5e-3411-44c5-9bc5-037358c47100"))

        game.board.add_player(player1)
        game.board.add_player(player2)
        game.board.add_player(player3)

        # test recursive method
        # Player 1 -> debt 50 Player2
        # Player 2 -> debt 50 Player3
        # Player 3 -> debt 30 Player1 -> debt 30 Player2

        player1.add_debt(
            creditor=player2,
            amount=50
        )

        player2.add_debt(
            creditor=player3,
            amount=50
        )

        player3.add_debt(
            creditor=player1,
            amount=30
        )

        player3.add_debt(
            creditor=player2,
            amount=20
        )

        game.player_balance_receive(player=player1,
                                    amount=50,
                                    reason="test")

        assert not player1.has_debts()
        assert not player2.has_debts()
        assert not player3.has_debts()

        assert player1.money == 30
        assert player2.money == 20
        assert player3.money == 0

    def test_process_card_actions(self):
        game = game_instance_overwrited()
        player1 = Player(bot=False,
                         user=User(id="183e1f5e-3411-44c5-9bc5-037358c47100",
                                   name="player1"))
        player2 = Player(bot=False,
                         user=User(id="523e1f5e-3411-44c5-9bc5-037358c47100",
                                   name="player2"))
        player3 = Player(bot=False,
                         user=User(id="612e1f5e-3411-44c5-9bc5-037358c47100",
                                   name="player3"))

        game.board.add_player(player1)
        game.board.add_player(player2)
        game.board.add_player(player3)

        card = Card(
            id_=1,
            action_type=CardActionType.RECEIVE_BANK,
            action_value=50
        )

        game.process_card_actions(player=player1,
                                  card=card)

        assert player1.money == 50

        card = Card(
            id_=2,
            action_type=CardActionType.GIVE_BOARD,
            action_value=50
        )

        game.process_card_actions(player=player1,
                                  card=card)

        assert player1.money == 0
        assert game.board.board_money == 50

        # TODO:
        card = Card(
            id_=3,
            action_type=CardActionType.MOVE_BACKWARD,
            action_value=3
        )
        card = Card(
            id_=4,
            action_type=CardActionType.GOTO_POSITION,
            action_value=4
        )
        card = Card(
            id_=5,
            action_type=CardActionType.GOTO_JAIL
        )

        card = Card(
            id_=6,
            action_type=CardActionType.GIVE_ALL,
            action_value=50
        )

        assert not player1.has_debts()

        game.process_card_actions(player=player1,
                                  card=card)

        assert player1.money == 0
        assert player1.has_debts()
        assert len(player1.debts) == 2
        assert player1.get_total_debts() == 100
        assert player2.money == 0
        assert player3.money == 0

        card = Card(
            id_=7,
            action_type=CardActionType.RECEIVE_ALL,
            action_value=50
        )

        # Player1 has two debts: 50 for player2, 50 for player3
        # Here the player should receive 50 from all players (player2,3)
        game.process_card_actions(player=player1,
                                  card=card)

        assert player1.money == 0
        assert player2.money == 0
        assert player3.money == 0

        assert not player3.has_debts()
        assert not player2.has_debts()
        assert not player1.has_debts()

        card = ChanceCard(
            id_=8,
            action_type=CardActionType.LEAVE_JAIL
        )

        game.process_card_actions(player=player1,
                                  card=card)

        assert player1.jail_cards['chance']
        assert not card.available

        card = CommunityCard(
            id_=8,
            action_type=CardActionType.LEAVE_JAIL
        )

        game.process_card_actions(player=player1,
                                  card=card)

        assert player1.jail_cards['community']
        assert not card.available

    def test_load_json(self):
        assert len(self.engine.squares) != 0
        assert len(self.engine.chance_deck) != 0
        assert len(self.engine.community_deck) != 0

        squares_path = os.path.join(settings.STATIC_ROOT, 'data/squares.json')
        with open(squares_path) as squares_file:
            squares = json.load(squares_file)
            assert len(self.engine.squares) == len(squares)

        cards_path = os.path.join(settings.STATIC_ROOT, 'data/cards.json')
        with open(cards_path) as cards_file:
            cards_json = json.load(cards_file)
            assert len(cards_json) == (len(self.engine.chance_deck) + len(
                self.engine.community_deck))
