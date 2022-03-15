from enum import Enum


class Card:
    id_: int
    description: str

    def __init__(self, id_: int, description: str):
        self.id_ = id_
        self.description = description


class ChanceCard(Card):
    def __init__(self, id_: int, description: str):
        super().__init__(id_, description)


class CommunityCard(Card):
    def __init__(self, id_: int, description: str):
        super().__init__(id_, description)
