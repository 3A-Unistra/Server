class Packet:
    def __init__(self, name):
        self.name = name

    def serialize(self) -> str:
        pass

    def deserialize(self) -> "Packet":
        pass
