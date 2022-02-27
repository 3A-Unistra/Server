from . import OwnableSquare, SquareType


class PropertySquare(OwnableSquare):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name, SquareType.Property)
