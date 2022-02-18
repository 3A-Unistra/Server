from . import OwnableSquare, SquareType


class CompanySquare(OwnableSquare):
    def __init__(self, name: str):
        super().__init__(name, SquareType.Company)
