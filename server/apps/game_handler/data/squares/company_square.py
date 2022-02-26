from . import OwnableSquare, SquareType


class CompanySquare(OwnableSquare):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name, SquareType.Company)
