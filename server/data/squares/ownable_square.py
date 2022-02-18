from . import Square, SquareType


class OwnableSquare(Square):
    def __init__(self, name: str, square_type: SquareType):
        super().__init__(name, square_type)
