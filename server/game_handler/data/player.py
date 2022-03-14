import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from server.game_handler.models import User


class Player:
    """
    This player class is used for bots as well as real players.
    Any offline player is a bot by default.

    To check if this Player is a "real" bot (not disconnected player bot),
    compare bot and online bool, if they are both True it is a "real" bot.
    """

    # Public id is for the id for bots
    public_id: str = None

    bot_name: str = None
    user: Optional[User]
    channel_name: str
    online: bool = False

    position: int = 0
    score: int = 0
    money: int = 0
    jail_turns: int = 0
    doubles: int = 0
    jail_cards = {
        'chance': False,
        'community': False
    }
    in_jail: bool = False
    bankrupt: bool = False
    bot: bool = True
    current_dices: Tuple[int, int]

    piece: int = 0

    # Bool for ping heartbeat, default value=True, for first heartbeat
    ping: bool = True
    ping_timeout: datetime

    # Temps values
    start_dice_throw_received: bool

    def __init__(self, user: Optional[User] = None, channel_name: str = None,
                 bot: bool = True,
                 bot_name: str = None):
        """
        :param bot: If this Player is a "real" bot
        """
        self.user = user
        self.bot = bot
        self.bot_name = bot_name
        self.channel_name = channel_name
        self.current_dices = (0, 0)
        self.start_dice_throw_received = False

        if bot is True:
            self.online = True
            self.public_id = str(uuid.uuid4())

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
            if self.user is None or self.user.name is None:
                return self.bot_name
            return 'Bot %s' % self.bot_name
        return self.user.name

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

    def dices_are_double(self) -> bool:
        return self.current_dices[0] == self.current_dices[1]

    def enter_prison(self):
        self.doubles = 0
        self.jail_turns = 0
        self.in_jail = True

    def exit_prison(self):
        self.doubles = 0
        self.jail_turns = 0
        self.in_jail = False

    def get_coherent_infos(self) -> dict:
        return {
            'player_token': self.get_id(),
            'name': self.get_name(),
            'bot': self.bot,
            'money': self.money,
            'position': self.position,
            'jail_turns': self.jail_turns,
            'jail_cards': self.jail_cards,
            'in_jail': self.in_jail,
            'bankrupt': self.bankrupt,
            'piece': self.piece
        }

    def get_id(self) -> str:
        """
        :return: Public_id if bot is a "real" bot, otherwise user.id
        """
        return self.public_id if self.bot and self.online else str(
            self.user.id)

    def __eq__(self, other):
        # For equality: player == other_player
        # Like: player.get_id() == other_player.get_id()
        if isinstance(other, Player):
            return self.get_id() == other.get_id()
        return False
