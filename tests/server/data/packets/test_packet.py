import json
from unittest import TestCase

from server.game_handler.data.packets import Packet, PacketUtils


class TestPacket(TestCase):

    def setUp(self):
        self.json_str = '{"name": "Exception"}'

    def test_serialize(self):
        packet = Packet(name='Exception')
        print(packet.serialize())
        assert packet.serialize() == self.json_str

    def test_deserialize(self):
        packet = PacketUtils.deserialize_packet(json.loads(self.json_str))
        assert packet.name == 'Exception'
