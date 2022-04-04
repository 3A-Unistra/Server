from server.game_handler.data import Player
from server.game_handler.data.squares import OwnableSquare


class Auction:
    square: OwnableSquare

    highest_bet: int
    highest_better: Player

    def __init__(self, player: Player):
        self.highest_bet = 0
        self.highest_better = player
