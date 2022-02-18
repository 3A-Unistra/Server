from enum import Enum


class CardType(Enum):
    Community = 0
    Chance = 1


class Card:
    id_: int
    card_type: CardType
    description: str

    def __init__(self, id_: int, card_type: CardType, description: str):
        self.id_ = id_
        self.card_type = card_type
        self.description = description
