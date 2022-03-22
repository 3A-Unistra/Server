from unittest import TestCase

from server.game_handler.consumers import PlayerConsumer, GameEngineConsumer


class TestMiddlewares(TestCase):

    def setUp(self):
        pass

    def test_player_consumer(self):
        cons = PlayerConsumer()
        assert cons is not None

    def test_game_engine_consumer(self):
        cons = GameEngineConsumer()
        assert cons is not None
