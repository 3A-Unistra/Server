from . import Square, SquareType


class CommunitySquare(Square):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Community)
