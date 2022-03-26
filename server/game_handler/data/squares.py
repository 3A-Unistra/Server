from enum import Enum
from typing import Optional

from server.game_handler.data import Player


class SquareType(Enum):
    GO = 0
    TAX = 1
    PROPERTY = 2
    STATION = 3
    COMPANY = 4
    JAIL = 5
    GO_TO_JAIL = 6
    PARKING = 7
    COMMUNITY = 8
    CHANCE = 9

    @staticmethod
    def has_value(value):
        return value in set(item.value for item in SquareType)


class Square:
    """
    Attributes:
        id_     Id
        name    Display name
    """

    id_: int

    def __init__(self, id_: int = 0):
        self.id_ = id_

    def deserialize(self, obj: dict):
        """
        Deserializes values needed
        :param obj: Json object
        """
        self.id_ = int(obj['id']) if 'id' in obj else 0


class OwnableSquare(Square):
    owner: Optional[Player]
    mortgaged: bool
    buy_price: int
    rent_base: int

    def __init__(self, id_: int = 0):
        super().__init__(id_)
        self.owner = None
        self.mortgaged = False
        self.buy_price = 0
        self.rent_base = 0

    def has_owner(self) -> bool:
        return self.owner is not None

    def get_rent(self) -> int:
        return self.rent_base

    def deserialize(self, obj: dict):
        super().deserialize(obj)
        self.buy_price = int(obj['buy_price'])
        self.rent_base = int(obj['rent_base'])


class ChanceSquare(Square):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class CommunitySquare(Square):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class CompanySquare(OwnableSquare):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class FreeParkingSquare(Square):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class StationSquare(OwnableSquare):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class TaxSquare(Square):
    tax_price: int = 0

    def __init__(self, id_: int = 0, tax_price: int = 0):
        super().__init__(id_)
        self.tax_price = tax_price


class GoSquare(Square):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class GoToJailSquare(Square):
    def __init__(self, id_: int = 0):
        super().__init__(id_)


class JailSquare(Square):
    pass


class PropertySquare(OwnableSquare):
    nb_house: int
    house_price: int  # same as hotel_price
    house_rents: {}

    def __init__(self, id_: int = 0, house_price: int = 0,
                 house_rents: {} = None):
        super().__init__(id_)
        self.nb_house = 0
        self.house_price = house_price
        self.house_rents = house_rents

    def get_rent(self) -> int:
        # TODO
        pass

    def has_hotel(self):
        return self.nb_house > 4

    def deserialize(self, obj: dict):
        super().deserialize(obj)
        self.house_price = int(obj['house_price'])
        self.house_rents = {}

        for i in range(5):
            self.house_rents[i] = obj['rent_%d' % (i + 1)]


class SquareUtils:
    squares: dict = {
        SquareType.GO: GoSquare,
        SquareType.TAX: TaxSquare,
        SquareType.PROPERTY: PropertySquare,
        SquareType.STATION: StationSquare,
        SquareType.COMPANY: CompanySquare,
        SquareType.JAIL: JailSquare,
        SquareType.GO_TO_JAIL: GoToJailSquare,
        SquareType.PARKING: FreeParkingSquare,
        SquareType.COMMUNITY: CommunitySquare,
        SquareType.CHANCE: ChanceSquare
    }

    @staticmethod
    def is_square(obj: dict) -> bool:
        return 'id' in obj and 'type' in obj

    @staticmethod
    def load_from_json(obj: dict) -> Optional["Square"]:
        """
        Loads json data and returns correct instance
        :param obj: Json data object
        :return: Square instance or None
        """
        if not SquareUtils.is_square(obj):
            return None

        # Check if type exists
        if not SquareType.has_value(obj['type']):
            return None

        square_type = SquareType(int(obj['type']))
        square = SquareUtils.squares[square_type]()

        # Deserialize remaining data
        square.deserialize(obj)

        return square
