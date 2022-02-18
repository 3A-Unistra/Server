from . import Square, SquareType


class ChanceSquare(Square):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Chance)
