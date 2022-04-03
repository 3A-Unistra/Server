from datetime import datetime
from enum import Enum
from typing import Optional, List

from server.game_handler.data import Player, Card
from server.game_handler.data.squares import OwnableSquare


class ExchangeState(Enum):
    # Start exchange (selecting player & property)
    STARTED = 0

    # Waiting select only property (if counter counter)
    WAITING_SELECT = 1

    # Waiting response from selected_player
    WAITING_RESPONSE = 2

    # Waiting counter selecting property
    WAITING_COUNTER_SELECT = 3

    # Waiting response from player
    WAITING_COUNTER_RESPONSE = 4

    # Finished
    FINISHED = 5


class Exchange:
    player: Player
    selected_player: Optional[Player]

    player_squares: List[OwnableSquare]
    player_cards: List[Card]
    player_money: int

    selected_player_squares: List[OwnableSquare]
    selected_player_cards: List[Card]
    selected_player_money: int

    state: ExchangeState
    timeout: datetime

    def __init__(self, player: Player,
                 selected_player: Optional[Player] = None):
        self.player = player
        self.selected_player = selected_player
        self.player_squares = []
        self.player_cards = []
        self.player_money = 0
        self.selected_player_squares = []
        self.selected_player_cards = []
        self.selected_player_money = 0
        self.state = ExchangeState.STARTED

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()

    def player_has_changes(self) -> bool:
        return self.player_money != 0 \
               or len(self.player_squares) != 0 \
               or len(self.player_cards) != 0

    def selected_player_has_changes(self) -> bool:
        return self.selected_player_money != 0 \
               or len(self.selected_player_squares) != 0 \
               or len(self.selected_player_cards) != 0

    def clear_selected_player(self):
        self.selected_player_money = 0
        self.selected_player_cards = []
        self.selected_player_squares = []

    def can_send(self) -> bool:
        return self.player_has_changes() or self.selected_player_has_changes()

    def add_or_remove_card(self, card: Card, recipient: bool = False):

        if recipient:
            if card in self.selected_player_cards:
                self.selected_player_cards.remove(card)
            else:
                self.selected_player_cards.append(card)
            return

        if card in self.player_cards:
            self.player_cards.remove(card)
        else:
            self.player_cards.append(card)

    def add_or_remove_square(self, square: OwnableSquare,
                             recipient: bool = False):

        if recipient:
            if square in self.selected_player_squares:
                self.selected_player_squares.remove(square)
            else:
                self.selected_player_squares.append(square)
            return

        if square in self.player_squares:
            self.player_squares.remove(square)
        else:
            self.player_squares.append(square)
