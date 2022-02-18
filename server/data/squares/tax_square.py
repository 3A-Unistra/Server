from . import Square, SquareType


class TaxSquare(Square):
    tax_price: int = 0

    def __init__(self, id_: int, name: str, tax_price: int):
        super().__init__(id_, name, SquareType.Tax)
        self.tax_price = tax_price
