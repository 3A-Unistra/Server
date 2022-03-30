from datetime import datetime
from typing import Optional

from server.game_handler.data import Player
from server.game_handler.data.squares import OwnableSquare


class Exchange:
    player: Player
    selected_player: Optional[Player]
    selected_square: Optional[OwnableSquare]

    timeout: datetime
    sent: bool

    def __init__(self, player: Player,
                 selected_player: Optional[Player] = None,
                 selected_square: Optional[OwnableSquare] = None):
        self.player = player
        self.selected_player = selected_player
        self.selected_square = selected_square
        self.sent = False

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()
