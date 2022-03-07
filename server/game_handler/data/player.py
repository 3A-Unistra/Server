from enum import Enum

from server.game_handler.models import User


class PlayerState(Enum):
    Paying = 0
    Jail = 1
    Bankrupt = 2
    Bot = 3


class Player:
    id_: int
    name: str
    position: int = 0
    score: int = 0
    money: int = 0
    jail_turns: int = 0
    state: PlayerState
    user: User

    def __init__(self, id_: int, name: str):
        self.id_ = id_
        self.name = name
