from . import Square, SquareType


class OwnableSquare(Square):
    def __init__(self, id_: int, name: str, square_type: SquareType):
        super().__init__(id_, name, square_type)
