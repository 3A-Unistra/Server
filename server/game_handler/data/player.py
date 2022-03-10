from enum import Enum

from server.game_handler.models import User


class PlayerState(Enum):
    Paying = 0
    Jail = 1
    Bankrupt = 2


class Player:
    """
    This player class is used for bots as well as real players

    To check if this Player is a "real" bot (not disconnected player bot),
    compare bot and online bool, if they are both True it is a "real" bot.
    """
    id_: str
    name: str
    position: int = 0
    score: int = 0
    money: int = 0
    jail_turns: int = 0
    state: PlayerState
    user: User
    bot: bool = False
    online: bool = False

    def __init__(self, id_: str, name: str, bot: bool = False):
        """
        :param id_: Id of the Player
        :param name: Name of the Player
        :param bot: If this Player is a "real" bot
        """
        self.id_ = id_
        self.name = name
        self.bot = bot

    def connect(self):
        """
        When player connects (disables bot)
        """
        self.online = True
        self.bot = False

    def disconnect(self):
        """
        When player disconnects (enables bot)
        """
        self.online = False
        self.bot = True
