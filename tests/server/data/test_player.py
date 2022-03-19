from unittest import TestCase

from server.game_handler.data import Player
from server.game_handler.data.player import PlayerDebt
from server.game_handler.models import User


class TestPacket(TestCase):

    def test_connect(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player.connect()
        assert player.bot is False
        assert player.online is True

    def test_disconnect(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player.disconnect()
        assert player.bot is True
        assert player.online is False

    def test_bot(self):
        player = Player()
        assert player.bot is True
        assert player.online is True

    def test_get_name(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100",
                                  name="Test"))
        assert player.get_name() == "Test"

        player.connect()

        assert player.get_name() == "Test"

        player.disconnect()

        assert player.get_name() == "Bot Test"

    def test_roll_dices(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))

        player.roll_dices()

        assert 0 < player.current_dices[0] <= 6
        assert 0 < player.current_dices[1] <= 6

    def test_dices_value(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player.current_dices = (1, 2)

        assert player.dices_value() == 3

    def test_dices_are_double(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player.current_dices = (1, 2)

        assert not player.dices_are_double()

        player.current_dices = (1, 1)

        assert player.dices_are_double()

    def test_enter_prison(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player.enter_prison()
        assert player.doubles == 0
        assert player.jail_turns == 0
        assert player.in_jail

    def test_exit_prison(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player.exit_prison()
        assert player.doubles == 0
        assert player.jail_turns == 0
        assert not player.in_jail

    def test_get_coherent_infos(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100",
                                  name="Test"))

        infos = player.get_coherent_infos()

        assert infos['player_token'] == "283e1f5e-3411-44c5-9bc5-037358c47100"
        assert infos['name'] == "Test"
        assert not infos['bot']
        assert infos['money'] == 0
        assert infos['position'] == 0
        assert infos['jail_turns'] == 0
        assert infos['jail_cards'] == {
            'community': False,
            'chance': False
        }
        assert not infos['in_jail']
        assert not infos['bankrupt']
        assert infos['piece'] == 0

    def test_get_id(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        assert player.get_id() == "283e1f5e-3411-44c5-9bc5-037358c47100"

    def test_get_debts_for(self):
        player = Player(bot=False,
                        user=User(id="283e1f5e-3411-44c5-9bc5-037358c47100"))
        player2 = Player(bot=False,
                         user=User(id="173e1f5e-3411-44c5-9bc5-037358c47100"))
        player.debts.append(PlayerDebt(creditor=player2, amount=10))


        debts = player.get_debts_for(player2)
        assert len(debts) == 1
        assert debts[0].amount == 10
