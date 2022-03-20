from unittest import TestCase

from server.game_handler.engine import Engine, Game, GameState


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
