import collections
import random
import uuid
from datetime import datetime
from typing import Optional, Tuple, List, Deque

from server.game_handler.models import User


class PlayerDebt:
    """
    When creditor is None, creditor is the bank
    """
    creditor: Optional["Player"]
    amount: int
    reason: str

    def __init__(self, creditor: Optional["Player"], amount: int = 0,
                 reason: str = ""):
        self.creditor = creditor
        self.amount = amount
        self.reason = reason

    def __str__(self):
        name = self.creditor.get_name() if self.creditor \
                                           is not None else "BANK"
        return "%d for %s" % (self.amount, name)


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
    bot_level: int = 0
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
    bankrupt: bool = False  # True when player defeated
    bot: bool = True
    current_dices: Tuple[int, int]

    piece: int = 0

    # Bool for ping heartbeat, default value=True, for first heartbeat
    ping: bool = True
    ping_timeout: datetime

    # Temp values
    start_dice_throw_received: bool

    # Dept system
    debts: Deque[PlayerDebt]

    def __init__(self, user: Optional[User] = None, channel_name: str = None,
                 bot: bool = True, bot_name: str = None, bot_level: int = 0):
        """
        :param bot: If this Player is a "real" bot
        """
        self.user = user
        self.bot = bot
        self.bot_name = bot_name
        self.bot_level = bot_level
        self.channel_name = channel_name
        self.current_dices = (0, 0)
        self.start_dice_throw_received = False
        self.debts = collections.deque()

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
            return 'Bot %s' % self.user.name
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

    def has_enough_money(self, price: int) -> bool:
        """
        :param price: Money to pay
        :return: Player has enough money
        """
        return self.money >= price

    def is_bankrupt(self) -> bool:
        """
        A player is bankrupt if he has debts
        :return: Player is bankrupt or not
        """
        return self.get_total_debts() > 0

    def has_debts(self) -> bool:
        return self.is_bankrupt()

    def add_debt(self, creditor: Optional["Player"], amount: int,
                 reason: str = ""):
        self.debts.append(PlayerDebt(
            creditor=creditor,
            amount=amount,
            reason=reason
        ))

    def get_debts_for(self, creditor: Optional["Player"]):
        return [a for a in self.debts if a.creditor == creditor]

    def get_total_debts(self) -> int:
        """
        :return: Total debts
        """
        return sum([debt.amount for debt in self.debts])

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
        if other is None:
            return False
        if isinstance(other, Player):
            return self.get_id() == other.get_id()
        return False
