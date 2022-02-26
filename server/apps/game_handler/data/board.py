from typing import List

from . import Card
from .squares import Square


class Board:
    board: List[Square]
    community_deck: List[Card]
    chance_deck: List[Card]
    prison_square: int
    board_money: int

    def __init__(self):
        pass
