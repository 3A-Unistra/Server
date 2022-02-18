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
    def __init__(self, name: str, square_type: SquareType):
        self.name = name
        self.square_type = square_type
