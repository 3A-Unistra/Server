import json

from server.data.exceptions import PacketException


class Packet:
    def __init__(self, name):
        self.name = name

    def serialize(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def deserialize(self, obj: object) -> "Packet":
        pass

    @staticmethod
    def deserialize_packet(json_str: str) -> "Packet":
        obj = json.loads(json_str)

        if 'name' not in obj:
            raise PacketException('Could not deserialize packet %s' % json_str)

        packet_name = obj['name']
        packet = Packet(packet_name)

        if packet_name == 'example':
            pass

        return packet
