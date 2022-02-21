from unittest import TestCase

from server.data.packets import Packet


class TestPacket(TestCase):
    def test_serialize(self):
        packet = Packet(name='TestPacket')
        assert packet.serialize() == '{"packet_name":"TestPacket"}'

    def test_deserialize(self):
        packet = Packet.deserialize_packet('{"packet_name":"TestPacket"}')
        assert packet.name == 'TestPacket'
