from datetime import datetime, timedelta

from server.game_handler.data import Player
from server.game_handler.data.squares import OwnableSquare


class Auction:
    square: OwnableSquare

    highest_bid: int
    highest_bidder: Player

    timeout: datetime
    tour_duration: int
    tour_remaining_seconds: int

    def __init__(self, player: Player, tour_duration: int = 0,
                 highest_bet: int = 0):
        self.highest_bid = highest_bet
        self.highest_bidder = player
        self.tour_duration = tour_duration
        self.tour_remaining_seconds = 0
        self.highest_bid = 0

    def set_timeout(self, seconds: int):
        self.timeout = datetime.now() + timedelta(seconds=seconds)

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()

    def bid(self, player: Player, bid: int) -> bool:
        """
        Processing a new bid
        :param player: Bidder
        :param bid: Player's bid
        :return: Bid accepted
        """
        if bid <= self.highest_bid:
            return False

        if not player.has_enough_money(bid):
            return False

        self.set_timeout(seconds=self.tour_duration)
        self.highest_bid = bid
        self.highest_bidder = player
        return True
