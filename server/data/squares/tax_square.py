from . import Square, SquareType


class TaxSquare(Square):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Tax)
