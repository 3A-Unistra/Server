from . import Square, SquareType


class GoSquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name, SquareType.Go)
