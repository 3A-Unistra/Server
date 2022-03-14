class Square:
    """
    Attributes:
        id_     Id
        name    Display name
    """

    id_: int
    name: str

    def __init__(self, id_: int, name: str):
        self.id_ = id_
        self.name = name


class OwnableSquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class ChanceSquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class CommunitySquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class CompanySquare(OwnableSquare):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class FreeParkingSquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class StationSquare(OwnableSquare):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class TaxSquare(Square):
    tax_price: int = 0

    def __init__(self, id_: int, name: str, tax_price: int):
        super().__init__(id_, name)
        self.tax_price = tax_price


class GoSquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class GoToJailSquare(Square):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)


class PropertySquare(OwnableSquare):
    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)
