from unittest import TestCase

from server.game_handler.data import Player, Board


class TestPacket(TestCase):
    board: Board

    def setUp(self):
        self.board = Board()

    def test_board_add_player(self):
        player = Player("283e1f5e-3411-44c5-9bc5-037358c47100", name="Test")
        self.board.add_player(player)
        assert len(self.board.players) == 1
        self.board.remove_player(player)

    def test_board_players_offline(self):
        player1 = Player("283e1f5e-3411-44c5-9bc5-037358c47100", name="Test1",
                         bot=False)
        player2 = Player("153e1f5e-3411-32c5-9bc5-037358c47100", name="Test2",
                         bot=False)
        player3 = Player("413e1f2e-3411-32c5-9bc5-037358c47120", name="Test3",
                         bot=False)
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
        player1 = Player("413e1f2e-3411-32c5-9bc5-037358c47120", name="Test",
                         bot=False)
        self.board.add_player(player1)
        assert self.board.player_exists(player1.id_)
        self.board.remove_player(player1)

    def test_board_players_online(self):
        player1 = Player("283e1f5e-3411-44c5-9bc5-037358c47100", name="Test1",
                         bot=False)
        player2 = Player("153e1f5e-3411-32c5-9bc5-037358c47100", name="Test2",
                         bot=False)
        player3 = Player("413e1f2e-3411-32c5-9bc5-037358c47120", name="Test3",
                         bot=False)
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
        player1 = Player("283e1f5e-3411-44c5-9bc5-037358c47100", name="Test1",
                         bot=False)
        player2 = Player("153e1f5e-3411-32c5-9bc5-037358c47100", name="Test2",
                         bot=False)
        player3 = Player("413e1f2e-3411-32c5-9bc5-037358c47120", name="Test3",
                         bot=False)
        self.board.add_player(player1)
        self.board.add_player(player2)
        self.board.add_player(player3)
        self.board.players_nb = 3
        assert self.board.get_current_player().id_ == player1.id_
        assert self.board.next_player().id_ == player2.id_
        assert self.board.next_player().id_ == player3.id_
        assert self.board.next_player().id_ == player1.id_
        player2.bankrupt = True
        assert self.board.next_player().id_ == player3.id_
        player3.bankrupt = True
        assert self.board.next_player().id_ == player1.id_
        assert self.board.next_player().id_ == player1.id_
        self.board.current_player_index = 0
        self.board.players_nb = 0
        self.board.remove_player(player1)
        self.board.remove_player(player2)
        self.board.remove_player(player3)

    def test_board_get_highest_dice(self):
        player1 = Player("283e1f5e-3411-44c5-9bc5-037358c47100", name="Test1",
                         bot=False)
        player2 = Player("153e1f5e-3411-32c5-9bc5-037358c47100", name="Test2",
                         bot=False)
        player3 = Player("413e1f2e-3411-32c5-9bc5-037358c47120", name="Test3",
                         bot=False)
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
        assert highest.id_ == player3.id_

        # Test same dice score
        player2.current_dices = (2, 3)

        assert self.board.get_highest_dice() is None

        self.board.remove_player(player1)
        self.board.remove_player(player2)
        self.board.remove_player(player3)
