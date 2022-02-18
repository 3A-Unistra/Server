from . import Square, SquareType


class FreeParkingSquare(Square):
    def __init__(self, name: str):
        super().__init__(name, SquareType.FreeParking)
