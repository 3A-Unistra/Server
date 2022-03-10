from unittest import TestCase

from server.game_handler.data import Player


class TestPacket(TestCase):

    def test_player_connect(self):
        player = Player("test", "test")
        player.connect()
        assert player.bot is False
        assert player.online is True

    def test_player_disconnect(self):
        player = Player("test", "test")
        player.disconnect()
        assert player.bot is True
        assert player.online is False

    def test_bot(self):
        player = Player("test_bot", "test_bot", bot=True)
        assert player.bot is True
        assert player.online is True
