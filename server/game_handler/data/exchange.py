from datetime import datetime
from typing import Optional

from server.game_handler.data import Player


class Exchange:
    player_from: Player
    player_to: Player
    property_id: int

    timeout: datetime

    def __init__(self, player_from: Player, player_to: Optional[Player],
                 property_id: int):
        self.player_from = player_from
        self.player_to = player_to
        self.property_id = property_id

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()
