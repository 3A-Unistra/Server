from datetime import datetime
from enum import Enum
from typing import Optional

from server.game_handler.data import Player
from server.game_handler.data.squares import OwnableSquare


class ExchangeState(Enum):
    CREATED = 0
    WAITING_ACCEPT = 1
    WAITING_ACCEPT_COUNTER = 2


class Exchange:
    player: Player
    selected_player: Optional[Player]
    selected_square: Optional[OwnableSquare]

    timeout: datetime

    def __init__(self, player: Player,
                 selected_player: Optional[Player] = None,
                 selected_square: Optional[OwnableSquare] = None):
        self.player = player
        self.selected_player = selected_player
        self.selected_square = selected_square

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()
