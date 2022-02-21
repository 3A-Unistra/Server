import json

from server.data.exceptions import PacketException


class Packet:
    def __init__(self, name):
        self.name = name

    def serialize(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def deserialize(self, obj: object) -> "Packet":
        pass

    @staticmethod
    def deserialize_packet(json_str: str) -> "Packet":
        obj = json.loads(json_str)

        if 'packet_name' in obj:
            raise PacketException('Could not deserialize packet %s' % json_str)

        packet_name = obj['packet_name']
        packet = Packet(packet_name)

        if packet_name is 'example':
            pass

        return packet
