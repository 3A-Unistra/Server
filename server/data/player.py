from enum import Enum


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

    def __init__(self, id_: int, name: str):
        self.id_ = id_
        self.name = name
