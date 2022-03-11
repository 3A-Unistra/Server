import json
from unittest import TestCase

from server.game_handler.data.packets import PacketUtils, ActionBuyHouse, \
    ExceptionPacket, GameStartDiceResults


class TestPacket(TestCase):

    def setUp(self):
        self.json_str = '{"code": 4000, "name": "Exception"}'
        self.args_json_str = '{"id_house": "test", "id_player": "test",' \
                             ' "name": "ActionBuyHouse"}'
        self.game_dice_json_str = '{"dice_result": [{"dice1": 2, "dice2": ' \
                                  '3, "player_token": ' \
                                  '"283e1f5e-3411-44c5-9bc5-037358c47100", ' \
                                  '"win": true}, {"dice1": 2, "dice2": 2, ' \
                                  '"player_token": ' \
                                  '"23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
                                  '"win": false}], "name": ' \
                                  '"GameStartDiceResults"}'

    def test_serialize(self):
        packet = ExceptionPacket()
        assert packet.serialize() == self.json_str

    def test_deserialize(self):
        packet = PacketUtils.deserialize_packet(json.loads(self.json_str))
        assert packet.name == 'Exception'

    def test_serialize_with_variables(self):
        packet = ActionBuyHouse(id_player="test", id_house="test")
        assert packet.serialize() == self.args_json_str

    def test_deserialize_with_variables(self):
        packet = PacketUtils.deserialize_packet(json.loads(self.args_json_str))
        assert isinstance(packet, ActionBuyHouse)
        assert packet.name == 'ActionBuyHouse'
        assert packet.id_house == 'test'
        assert packet.id_player == 'test'

    def test_serialize_game_start_dice_results(self):
        packet = GameStartDiceResults()
        packet.add_dice_result(
            player_token='283e1f5e-3411-44c5-9bc5-037358c47100',
            dice1=2,
            dice2=3,
            win=True)

        packet.add_dice_result(
            player_token='23b3a6c7-6990-44b1-b466-8f8c3da5ec7d',
            dice1=2,
            dice2=2,
            win=False)

        assert packet.serialize() == self.game_dice_json_str

    def test_deserialize_game_start_dice_results(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.game_dice_json_str))
        assert isinstance(packet, GameStartDiceResults)
        assert packet.name == 'GameStartDiceResults'
        assert len(packet.dice_result) == 2

        # Player tokens
        assert 'player_token' in packet.dice_result[0]
        assert 'player_token' in packet.dice_result[1]
        assert packet.dice_result[0][
                   'player_token'] == '283e1f5e-3411-44c5-9bc5-037358c47100'
        assert packet.dice_result[1][
                   'player_token'] == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

        # Dice1
        assert 'dice1' in packet.dice_result[0]
        assert 'dice1' in packet.dice_result[1]
        assert packet.dice_result[0]['dice1'] == 2
        assert packet.dice_result[1]['dice1'] == 2

        # Dice2
        assert 'dice2' in packet.dice_result[0]
        assert 'dice2' in packet.dice_result[1]
        assert packet.dice_result[0]['dice2'] == 3
        assert packet.dice_result[1]['dice2'] == 2

        # Win
        assert 'win' in packet.dice_result[0]
        assert 'win' in packet.dice_result[1]
        assert packet.dice_result[0]['win'] is True
        assert packet.dice_result[1]['win'] is False
