from . import Square, SquareType


class GoToJailSquare(Square):
    def __init__(self, name: str):
        super().__init__(name, SquareType.GoToJail)
