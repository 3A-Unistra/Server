from unittest import TestCase

from server.apps.game_handler.data.packets import Packet


class TestPacket(TestCase):

    def setUp(self):
        self.json_str = '{"name": "TestPacket"}'

    def test_serialize(self):
        packet = Packet(name='TestPacket')
        print(packet.serialize())
        assert packet.serialize() == self.json_str

    def test_deserialize(self):
        packet = Packet.deserialize_packet(self.json_str)
        assert packet.name == 'TestPacket'
