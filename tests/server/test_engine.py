from unittest import TestCase

from server.game_handler.data import Player
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




