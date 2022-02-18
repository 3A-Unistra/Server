from . import OwnableSquare, SquareType


class StationSquare(OwnableSquare):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Station)
