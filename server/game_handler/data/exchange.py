from datetime import datetime
from enum import Enum
from typing import Optional

from server.game_handler.data import Player
from server.game_handler.data.squares import OwnableSquare


class ExchangeState(Enum):
    STARTED = 0
    WAITING_SELECT = 1
    WAITING_RESPONSE = 2
    WAITING_COUNTER_SELECT = 3
    WAITING_COUNTER_RESPONSE = 4
    FINISHED = 5


class Exchange:
    player: Player
    selected_player: Optional[Player]
    selected_square: Optional[OwnableSquare]

    state: ExchangeState
    timeout: datetime

    def __init__(self, player: Player,
                 selected_player: Optional[Player] = None,
                 selected_square: Optional[OwnableSquare] = None):
        self.player = player
        self.selected_player = selected_player
        self.selected_square = selected_square
        self.state = ExchangeState.STARTED

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()
