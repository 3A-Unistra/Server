import json
from unittest import TestCase

from server.game_handler.data.packets import PacketUtils, ActionBuyHouse, \
    ExceptionPacket


class TestPacket(TestCase):

    def setUp(self):
        self.json_str = '{"code": 4000, "name": "Exception"}'
        self.args_json_str = '{"id_house": "test", "id_player": "test",' \
                             ' "name": "ActionBuyHouse"}'

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
