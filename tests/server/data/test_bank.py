from unittest import TestCase

from server.game_handler.data import Bank


class TestBank(TestCase):

    def setUp(self):
        pass

    def test_bank(self):
        bank = Bank(10, 5)

        assert bank.nb_house == 10
        assert bank.nb_hotel == 5

        bank.buy_house()
        assert bank.nb_house == 9

        bank.buy_hotel()
        assert bank.nb_hotel == 4

        bank.sell_house()
        assert bank.nb_house == 10

        bank.sell_hotel()
        assert bank.nb_hotel == 5

        assert bank.has_houses()
        assert bank.has_hotels()
