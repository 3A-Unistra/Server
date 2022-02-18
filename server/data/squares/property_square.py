from . import OwnableSquare, SquareType


class PropertySquare(OwnableSquare):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Property)
