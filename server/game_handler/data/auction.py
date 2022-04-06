from datetime import datetime, timedelta

from server.game_handler.data import Player
from server.game_handler.data.squares import OwnableSquare


class Auction:
    square: OwnableSquare

    highest_bet: int
    highest_better: Player

    timeout: datetime
    tour_remaining_seconds: float

    def __init__(self, player: Player, highest_bet: int = 0):
        self.highest_bet = highest_bet
        self.highest_better = player
        self.tour_action_remaining_seconds = 0

    def set_timeout(self, seconds: int):
        self.timeout = datetime.now() + timedelta(seconds=seconds)

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()
