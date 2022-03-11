import random
import uuid
from enum import Enum
from typing import Optional, Tuple

from server.game_handler.models import User


class PlayerState(Enum):
    Paying = 0
    Jail = 1
    Bankrupt = 2


class Player:
    """
    This player class is used for bots as well as real players.
    Any offline player is a bot by default.

    To check if this Player is a "real" bot (not disconnected player bot),
    compare bot and online bool, if they are both True it is a "real" bot.
    """
    id_: str
    public_id: str
    name: str
    bot_name: str = None
    position: int = 0
    score: int = 0
    money: int = 0
    jail_turns: int = 0
    state: PlayerState
    user: Optional[User]
    bot: bool = True
    online: bool = False
    channel_name: str
    current_dices: Tuple[int, int]

    def __init__(self, id_: str, name: str, channel_name: str = None,
                 bot: bool = True,
                 bot_name: str = None):
        """
        :param id_: Id of the Player
        :param name: Name of the Player
        :param bot: If this Player is a "real" bot
        """
        self.id_ = id_
        self.name = name
        self.bot = bot
        self.bot_name = bot_name
        self.user = None
        self.channel_name = channel_name
        self.current_dices = (0, 0)
        self.public_id = str(uuid.uuid4())

        if bot is True:
            self.online = True

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

    def get_name(self):
        """
        :return: Name of the Player
        """
        if self.bot:
            if self.name is None:
                return self.bot_name
            return 'Bot %s' % self.bot_name
        return self.name

    def roll_dices(self) -> int:
        """
        Roll dices
        :return: Sum of two dices
        """
        a = random.randint(1, 6)
        b = random.randint(1, 6)
        self.current_dices = (a, b)
        return a + b

    def dices_value(self) -> int:
        return sum(self.current_dices)
