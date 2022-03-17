from enum import Enum
from typing import Optional

from server.game_handler.data import Player


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
    owner: Optional[Player]
    mortgaged: bool
    price: int
    rent: int

    def __init__(self, id_: int, name: str):
        super().__init__(id_, name)
        self.owner = None

    def has_owner(self) -> bool:
        return self.owner is not None

    def get_rent(self) -> int:
        return self.rent


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
    nb_house: int
    house_cost: int
    house_rents: {}

    hotel_rent: int

    def __init__(self, id_: int, name: str, house_rents: {}):
        super().__init__(id_, name)
        self.house_rents = house_rents

    def get_rent(self) -> int:
        # TODO
        pass
