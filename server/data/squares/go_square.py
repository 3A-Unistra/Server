from . import Square, SquareType


class GoSquare(Square):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Go)
