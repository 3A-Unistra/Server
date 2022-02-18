from . import Square, SquareType


class CommunitySquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name, SquareType.Community)
