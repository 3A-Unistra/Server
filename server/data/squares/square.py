from enum import Enum


class SquareType(Enum):
    Go = 0
    FreeParking = 1
    GoToJail = 2
    Tax = 3
    Community = 4
    Chance = 5
    Station = 6
    Company = 7
    Property = 8


class Square:
    """
    Attributes:
        id_     Id
        name    Display name
        type    SquareType enum type
    """
    id_: int
    name: str
    type_: SquareType

    def __init__(self, id_: int, name: str, type_: SquareType):
        self.id_ = id_
        self.name = name
        self.type_ = type_
