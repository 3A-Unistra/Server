import enum
import json
from enum import Enum
from typing import Dict, List

from .exceptions import PacketException


class Packet:

    def __init__(self, name: str):
        self.name = name

    def serialize(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def deserialize(self, obj: object):
        pass


def convert_to_int(obj, key) -> int:
    """
    static function used in deserialization
    :param key: Key to get bool from
    :param obj: JSON deserialized object
    """
    if key not in obj:
        return 0
    try:
        return int(obj[key])
    except ValueError:
        return 0


def convert_to_bool(obj, key) -> bool:
    """
    static function used in deserialization
    :param key: Key to get bool from
    :param obj: JSON deserialized object
    """
    if key not in obj:
        return False
    try:
        return bool(obj[key])
    except ValueError:
        return False


class LobbyPacket(Packet):
    """
    Lobby packet => inherits Packet
    """
    name: str

    def __init__(self, name: str):
        self.name = name
        super().__init__(name)


class PlayerPacket(Packet):
    """
    Packet containing player_token to identify Player
    """
    player_token: str

    def __init__(self, name: str, player_token: str):
        super().__init__(name)
        self.player_token = player_token

    def deserialize(self, obj: object):
        if 'player_token' in obj:
            self.player_token = obj["player_token"]


class InternalPacket(Packet):
    """
    Packet for Internal communication
    """
    pass


class PlayerPropertyPacket(PlayerPacket):
    """
    Packet for player action on properties
    """
    property_id: int

    def __init__(self, name: str, player_token: str, property_id: int):
        super().__init__(name, player_token)
        self.property_id = property_id

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.property_id = int(obj['property_id']) \
            if 'property_id' in obj else 0


class InternalCheckPlayerValidity(InternalPacket):
    player_token: str
    valid: bool

    def __init__(self, player_token: str = "", valid: bool = False):
        super().__init__(name=self.__class__.__name__)
        self.player_token = player_token
        self.valid = valid

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.valid = convert_to_bool(obj, 'valid')


class InternalPlayerDisconnect(InternalPacket):
    player_token: str
    reason: str

    def __init__(self, player_token: str = "", reason: str = ""):
        super().__init__(name=self.__class__.__name__)
        self.player_token = player_token
        self.reason = reason

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.reason = obj['reason']


class PlayerValid(Packet):
    def __init__(self):
        super().__init__(self.__class__.__name__)


class PlayerLobbyPacket(PlayerPacket, LobbyPacket):
    pass


class EnterRoom(PlayerLobbyPacket):
    game_token: str
    password: str

    def __init__(self, player_token: str = "", game_token: str = "",
                 password: str = ""):
        super().__init__(self.__class__.__name__, player_token=player_token)
        self.game_token = game_token
        self.password = password

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.game_token = obj["game_token"] if "game_token" in obj else ""
        self.password = obj["password"] if "password" in obj else ""


class LaunchGame(PlayerLobbyPacket):

    def __init__(self, player_token: str = ""):
        super().__init__(self.__class__.__name__,
                         player_token=player_token)


class ExceptionPacket(Packet):
    code: int

    def __init__(self, code: int = 4000):
        super().__init__("Exception")
        self.code = code

    def deserialize(self, obj: object):
        self.code = convert_to_int(obj, "code")


class EnterRoomSucceed(LobbyPacket):
    piece: int
    game_token: str

    def __init__(self, game_token: str = "", piece: int = 0):
        super().__init__(self.__class__.__name__)
        self.piece = piece
        self.game_token = game_token

    def deserialize(self, obj: object):
        self.piece = convert_to_int(obj, "piece")
        self.game_token = obj["game_token"] if "game_token" in obj else ""


class LeaveRoom(LobbyPacket):
    player_token: str
    game_token: str

    def __init__(self, player_token: str = "", game_token: str = ""):
        super().__init__(self.__class__.__name__)
        self.player_token = player_token
        self.game_token = game_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token'] if 'player_token' in \
                                                   obj else ""
        self.game_token = obj['game_token'] if 'game_token' in obj else ""


class LeaveRoomSucceed(LobbyPacket):
    def __init__(self):
        super().__init__("LeaveRoomSucceed")


class UpdateReason(Enum):
    NEW_CONNECTION = 0
    NEW_PLAYER = 1
    PLAYER_LEFT = 2
    ROOM_DELETED = 3
    ROOM_CREATED = 4
    HOST_LEFT = 5
    LAUNCHING_GAME = 6
    NEW_BOT = 7
    DELETE_BOT = 8

    @staticmethod
    def has_value(value):
        return value in set(item.value for item in UpdateReason)


class StatusRoom(LobbyPacket):
    game_token: str
    game_name: str
    nb_players: int
    max_nb_players: int
    players: List[str]  # list of players
    option_auction: bool
    option_double_on_start: bool
    option_max_time: int
    option_max_rounds: int
    option_first_round_buy: bool
    starting_balance: int

    def __init__(self, game_token: str = "", game_name: str = "",
                 nb_players: int = 0, max_nb_players: int = 0,
                 players: List[str] = None, option_auction: bool = False,
                 option_double_on_start: bool = False,
                 option_max_time: int = 0, option_max_rounds: int = 0,
                 option_first_round_buy: bool = False,
                 starting_balance: int = 0):
        super().__init__(self.__class__.__name__)
        self.game_token = game_token
        self.game_name = game_name
        self.nb_players = nb_players
        self.max_nb_players = max_nb_players
        self.players = players
        self.option_auction = option_auction
        self.option_double_on_start = option_double_on_start
        self.option_max_time = option_max_time
        self.option_max_rounds = option_max_rounds
        self.option_first_round_buy = option_first_round_buy
        self.starting_balance = starting_balance

    def deserialize(self, obj: object):
        self.game_token = obj['game_token'] if 'game_token' in obj else ""
        self.game_name = obj['game_name'] if 'game_name' in obj else ""
        self.nb_players = convert_to_int(obj, 'nb_players')
        self.max_nb_players = convert_to_int(obj, 'max_nb_players')
        self.players = obj['players'] if 'players' in obj else []
        self.option_auction = convert_to_bool(obj, 'option_auction')
        self.option_double_on_start = convert_to_bool(obj, 'double_on_start')
        self.option_max_time = convert_to_bool(obj, 'option_max_time')
        self.option_max_rounds = convert_to_bool(obj, 'option_max_rounds')
        self.option_first_round_buy = \
            convert_to_bool(obj, 'option_first_round_buy')
        self.starting_balance = convert_to_int(obj, 'starting_balance')


class BroadcastNewRoomToLobby(LobbyPacket):
    game_token: str
    game_name: str
    nb_players: int
    max_nb_players: int
    is_private: bool
    has_password: bool

    def __init__(self, game_token: str = "", game_name: str = "",
                 nb_players: int = 0, max_nb_players: int = 0,
                 is_private: bool = False, has_password: bool = False):
        super().__init__(self.__class__.__name__)
        self.game_token = game_token
        self.game_name = game_name
        self.nb_players = nb_players
        self.max_nb_players = max_nb_players
        self.is_private = is_private
        self.has_password = has_password

    def deserialize(self, obj: object):
        self.game_token = obj['game_token'] if 'game_token' in obj else ""
        self.game_name = obj['game_name'] if 'game_name' in obj else ""
        self.nb_players = convert_to_int(obj, 'nb_players')
        self.max_nb_players = convert_to_int(obj, 'max_nb_players')
        self.is_private = convert_to_bool(obj, 'is_private')
        self.has_password = convert_to_bool(obj, 'has_password')


class BroadcastUpdateLobby(LobbyPacket):
    game_token: str
    reason: int

    def __init__(self, game_token: str = "",
                 reason: int = 0):
        super().__init__(self.__class__.__name__)
        self.game_token = game_token
        self.reason = reason

    def deserialize(self, obj: object):
        self.game_token = obj['game_token'] if 'game_token' in obj else 0
        self.reason = convert_to_int(obj, 'reason')


class BroadcastUpdateRoom(LobbyPacket):
    game_token: str
    nb_players: int
    player: str
    reason: int

    def __init__(self, game_token: str = "", nb_players: int = 0,
                 reason: int = 0, player: str = None):
        super().__init__(self.__class__.__name__)
        self.game_token = game_token
        self.nb_players = nb_players
        self.player = "" if player is None else player
        self.reason = reason

    def deserialize(self, obj: object):
        self.game_token = obj['game_token'] if 'game_token' in obj else ""
        self.nb_players = convert_to_int(obj, 'nb_players')
        self.player = obj['player'] if 'player' in obj else 0
        self.reason = convert_to_int(obj, 'reason')


class NewHost(LobbyPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__(self.__class__.__name__)
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj[
            'player_token'] if 'player_token' in obj else ""


class PingPacket(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__("Ping", player_token=player_token)


class AppletPrepare(LobbyPacket):
    def __init__(self):
        super().__init__(self.__class__.__name__)


class AppletReady(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class GameStart(Packet):
    """
    Contains all informations of current state
    """
    game_name: str
    options: {}
    players: []

    def __init__(self, game_name: str = "", options=None, players: [] = None):
        super().__init__(self.__class__.__name__)
        self.game_name = game_name
        self.options = {} if options is None else options
        self.players = [] if players is None else players

    def deserialize(self, obj: object):
        self.game_name = obj['game_name']
        self.options = obj['options']
        self.players = obj['players']


class PlayerDisconnect(PlayerPacket):
    reason: str

    def __init__(self, player_token: str = "", reason: str = ""):
        super().__init__(self.__class__.__name__,
                         player_token=player_token)
        self.reason = reason

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.reason = obj["reason"]


class PlayerReconnect(PlayerPacket):
    reason: str

    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class GameStartDice(Packet):
    def __init__(self):
        super().__init__(self.__class__.__name__)


class GameStartDiceThrow(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(self.__class__.__name__, player_token=player_token)


class GameStartDiceResults(Packet):
    dice_result: []

    def __init__(self, dice_result: [] = None):
        super().__init__(self.__class__.__name__)
        self.dice_result = [] if dice_result is None else dice_result

    def deserialize(self, obj: object):
        if 'dice_result' not in obj:
            return
        for o in obj['dice_result']:
            self.dice_result.append({
                'player_token': o['player_token'],
                'dice1': int(o['dice1']),
                'dice2': int(o['dice2']),
                'win': bool(o['win'])
            })

    def add_dice_result(self, player_token: str, dice1: int, dice2: int,
                        win: bool = False):
        """
        :param player_token: Player Token
        :param dice1: Result dice 1
        :param dice2: Result dice 2
        :param win: Player has win the start dice
        """
        self.dice_result.append({
            'player_token': player_token,
            'dice1': dice1,
            'dice2': dice2,
            'win': win
        })


class RoundStart(Packet):
    current_player: str

    def __init__(self, current_player: str = ""):
        super().__init__(self.__class__.__name__)
        self.current_player = current_player

    def deserialize(self, obj: object):
        self.current_player = obj['current_player']


class RoundDiceChoiceResult(Enum):
    ROLL_DICES = 0
    JAIL_PAY = 1
    JAIL_CARD_CHANCE = 2
    JAIL_CARD_COMMUNITY = 3

    @staticmethod
    def has_value(value):
        return value in set(item.value for item in RoundDiceChoiceResult)


class RoundDiceChoice(PlayerPacket):
    choice: int

    def __init__(self, player_token: str = "",
                 choice: RoundDiceChoiceResult = RoundDiceChoiceResult(0)):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.choice = choice.value

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.choice = convert_to_int(obj, 'choice')


class RoundDiceResults(PlayerPacket):
    result: int
    dice1: int
    dice2: int

    def __init__(self, player_token: str = "",
                 result: RoundDiceChoiceResult = RoundDiceChoiceResult(0),
                 dice1: int = 0,
                 dice2: int = 0):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.result = result.value
        self.dice1 = dice1
        self.dice2 = dice2

    def deserialize(self, obj: object):
        super().deserialize(obj)
        # TODO check enum validity
        self.result = convert_to_int(obj, 'result')
        self.dice1 = convert_to_int(obj, 'dice1')
        self.dice2 = convert_to_int(obj, 'dice2')


class PlayerMove(PlayerPacket):
    destination: int

    def __init__(self, player_token: str = "",
                 destination: int = 0):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.destination = destination

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.destination = convert_to_int(obj, 'destination')


class RoundRandomCard(PlayerPacket):
    card_id: int
    is_community: bool

    def __init__(self, player_token: str = "", card_id: int = 0,
                 is_community: bool = False):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.card_id = card_id
        self.is_community = is_community

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.card_id = convert_to_int(obj, 'card_id')
        self.is_community = convert_to_bool(obj, 'is_community')


class PlayerUpdateBalance(PlayerPacket):
    old_balance: int
    new_balance: int
    reason: str

    def __init__(
            self, player_token: str = "", old_balance: int = 0,
            new_balance: int = 0,
            reason: str = ""
    ):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.old_balance = old_balance
        self.new_balance = new_balance
        self.reason = reason

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.old_balance = convert_to_int(obj, 'old_balance')
        self.new_balance = convert_to_int(obj, 'new_balance')
        self.reason = obj['reason'] if 'reason' in obj else ""


class PlayerPayDebt(PlayerPacket):
    player_to: str
    amount: int
    reason: str

    def __init__(self, player_from: str = "", player_to: str = "",
                 amount: int = 0, reason: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_from)
        self.player_to = player_to
        self.amount = amount
        self.reason = reason

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.player_to = obj['player_to'] if 'player_to' in obj else ""
        self.amount = convert_to_int(obj, 'amount')
        self.reason = obj['reason'] if 'reason' in obj else ""


class PlayerEnterPrison(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class PlayerExitPrison(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionStart(Packet):
    def __init__(self):
        super().__init__(name=self.__class__.__name__)


class ActionEnd(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionTimeout(Packet):
    def __init__(self):
        super().__init__(name=self.__class__.__name__)


class ActionExchange(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchangeAccept(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchangePlayerSelect(PlayerPacket):
    selected_player_token: str

    def __init__(self, player_token: str = "",
                 selected_player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.selected_player_token = selected_player_token

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.selected_player_token = obj["selected_token"]


class ExchangeTradeSelectType(Enum):
    PROPERTY = 0
    MONEY = 1
    LEAVE_JAIL_COMMUNITY_CARD = 2
    LEAVE_JAIL_CHANCE_CARD = 3

    @staticmethod
    def has_value(value):
        return value in set(item.value for item in ExchangeTradeSelectType)


class ActionExchangeTradeSelect(PlayerPacket):
    exchange_type: int
    value: int
    update_affects_recipient: bool

    def __init__(self, player_token: str = "", value: int = 0,
                 exchange_type: ExchangeTradeSelectType
                 = ExchangeTradeSelectType(0),
                 update_affects_recipient: bool = False):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.value = value
        self.exchange_type = exchange_type.value
        self.update_affects_recipient = update_affects_recipient

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.value = convert_to_int(obj, 'value')

        if not ExchangeTradeSelectType.has_value(self.value):
            self.value = 0

        self.exchange_type = convert_to_int(obj, 'exchange_type')


class ActionExchangeSend(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchangeDecline(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchangeCounter(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchangeCancel(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ExchangeTransferType(Enum):
    PROPERTY = 0
    CARD = 1


class ActionExchangeTransfer(PlayerPacket):
    player_to: str
    value: int
    transfer_type: ExchangeTransferType

    def __init__(self, player_token: str = "", player_to: str = "",
                 value: int = 0, transfer_type: ExchangeTransferType
                 = ExchangeTransferType(0)):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.player_to = player_to
        self.value = value
        self.transfer_type = transfer_type

    def deserialize(self, obj: object):
        self.player_to = obj['player_to']
        self.value = convert_to_int(obj, 'value')
        self.transfer_type = obj['transfer_type']


class ActionAuctionProperty(PlayerPacket):
    min_bid: int

    def __init__(self, player_token: str = "", min_bid: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token)
        self.id_player = player_token
        self.min_bid = min_bid

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.min_bid = convert_to_int(obj, "min_bid")


class AuctionBid(PlayerPacket):
    bid: int

    def __init__(self, player_token: str = "", bid: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token)
        self.bid = bid

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.bid = convert_to_int(obj, "bid")


class AuctionEnd(PlayerPacket):
    highest_bid: int
    # Remaining time in seconds (action timeout)
    remaining_time: int

    def __init__(self, player_token: str = "", highest_bid: int = 0,
                 remaining_time: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token)
        self.highest_bid = highest_bid
        self.remaining_time = remaining_time


class ActionBuyProperty(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionBuyPropertySucceed(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionMortgageProperty(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionMortgageSucceed(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionUnmortgageProperty(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionUnmortgageSucceed(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionBuyHouse(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionBuyHouseSucceed(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionSellHouse(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


class ActionSellHouseSucceed(PlayerPropertyPacket):
    def __init__(self, player_token: str = "", property_id: int = 0):
        super().__init__(self.__class__.__name__,
                         player_token=player_token,
                         property_id=property_id)


# Lobby packets

class CreateGame(LobbyPacket):
    player_token: str
    password: str
    game_name: str
    max_nb_players: int
    starting_balance: int
    is_private: bool
    option_auction: bool
    option_double_on_start: bool
    option_max_time: int
    option_max_rounds: int
    option_first_round_buy: bool

    def __init__(self, player_token: str = "", password: str = "",
                 game_name: str = "", max_nb_players: int = 0,
                 is_private: bool = False, starting_balance: int = 0,
                 option_auction: bool = False,
                 option_double_on_start: bool = False,
                 option_max_time: int = 0,
                 option_max_rounds: int = 0,
                 option_first_round_buy: bool = False):
        super().__init__("CreateGame")
        self.player_token = player_token
        self.password = password
        self.max_nb_players = max_nb_players
        self.is_private = is_private
        self.starting_balance = starting_balance
        self.game_name = game_name
        self.option_auction = option_auction
        self.option_double_on_start = option_double_on_start
        self.option_max_time = option_max_time
        self.option_max_rounds = option_max_rounds
        self.option_first_round_buy = option_first_round_buy

    def deserialize(self, obj: object):
        self.player_token = obj['player_token'] if 'player_token' in \
                                                   obj else ""
        self.password = obj['password'] if 'password' in obj else ""
        self.max_nb_players = convert_to_int(obj, 'max_nb_players')
        self.is_private = convert_to_bool(obj, 'is_private')
        self.game_name = obj['game_name'] if 'game_name' in obj else ""
        self.option_auction = convert_to_bool(obj, 'option_auction')
        self.option_double_on_start = \
            convert_to_bool(obj, 'option_double_on_start')
        self.option_max_time = convert_to_bool(obj, 'option_max_time')
        self.option_max_rounds = convert_to_int(obj, 'option_max_rounds')
        self.option_first_round_buy = \
            convert_to_bool(obj, 'option_first_round_buy')


class CreateGameSucceed(LobbyPacket):
    player_token: str
    game_token: str
    piece: int

    def __init__(self, player_token: str = "", game_token: str = "",
                 piece: int = 0):
        super().__init__("CreateGameSucceed")
        self.player_token = player_token
        self.game_token = game_token
        self.piece = piece

    def deserialize(self, obj: object):
        self.player_token = obj['player_token'] if 'player_token' in obj else 0
        self.piece = convert_to_int(obj, 'piece')
        self.game_token = obj['game_token'] if 'game_token' in obj else ''


class AddBot(PlayerLobbyPacket):
    game_token: str
    bot_difficulty: int

    def __init__(self, player_token: str = "", game_token: str = "",
                 bot_difficulty: int = 0):
        super().__init__("AddBot", player_token=player_token)
        self.game_token = game_token
        self.bot_difficulty = bot_difficulty

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.bot_difficulty = convert_to_int(obj, 'bot_difficulty')
        self.game_token = obj['game_token']


class InternalLobbyConnect(InternalPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__("InternalLobbyConnect")
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']


class InternalLobbyDisconnect(InternalPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__("InternalLobbyDisconnect")
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']


class DeleteBot(LobbyPacket):
    bot_token: str

    def __init__(self, bot_token: str = ""):
        super().__init__("DeleteBot")

    def deserialize(self, obj: object):
        self.bot_token = obj['bot_token'] if 'bot_token' in obj else ""


class PacketUtils:
    packets = {
        # Utility packets
        "Exception": ExceptionPacket,
        "Ping": PingPacket,
        # Common packets
        "AppletPrepare": AppletPrepare,
        "AppletReady": AppletReady,
        "PlayerDisconnect": PlayerDisconnect,
        "PlayerReconnect": PlayerReconnect,
        "GameStartDice": GameStartDice,
        "GameStartDiceThrow": GameStartDiceThrow,
        "GameStartDiceResults": GameStartDiceResults,
        "RoundStart": RoundStart,
        "RoundDiceChoice": RoundDiceChoice,
        "RoundDiceResults": RoundDiceResults,
        "PlayerMove": PlayerMove,
        "RoundRandomCard": RoundRandomCard,
        "PlayerUpdateBalance": PlayerUpdateBalance,
        "PlayerPayDebt": PlayerPayDebt,
        "PlayerEnterPrison": PlayerEnterPrison,
        "PlayerExitPrison": PlayerExitPrison,
        # Tour actions
        "ActionStart": ActionStart,
        "ActionEnd": ActionEnd,
        "ActionTimeout": ActionTimeout,
        "ActionExchange": ActionExchange,
        "ActionExchangePlayerSelect": ActionExchangePlayerSelect,
        "ActionExchangeTradeSelect": ActionExchangeTradeSelect,
        "ActionExchangeSend": ActionExchangeSend,
        "ActionExchangeAccept": ActionExchangeAccept,
        "ActionExchangeDecline": ActionExchangeDecline,
        "ActionExchangeCounter": ActionExchangeCounter,
        "ActionExchangeCancel": ActionExchangeCancel,
        "ActionAuctionProperty": ActionAuctionProperty,
        "AuctionBid": AuctionBid,
        "AuctionEnd": AuctionEnd,
        "ActionBuyProperty": ActionBuyProperty,
        "ActionBuyPropertySucceed": ActionBuyPropertySucceed,
        "ActionMortgageProperty": ActionMortgageProperty,
        "ActionMortgageSucceed": ActionMortgageSucceed,
        "ActionUnmortgageProperty": ActionUnmortgageProperty,
        "ActionUnmortgageSucceed": ActionUnmortgageSucceed,
        "ActionBuyHouse": ActionBuyHouse,
        "ActionBuyHouseSucceed": ActionBuyHouseSucceed,
        "ActionSellHouse": ActionSellHouse,
        "ActionSellHouseSucceed": ActionSellHouseSucceed,
        "GameStart": GameStart,
        "PlayerValid": PlayerValid,
        # Lobby packets
        "EnterRoom": EnterRoom,
        "EnterRoomSucceed": EnterRoomSucceed,
        "LeaveRoom": LeaveRoom,
        "LeaveRoomSucceed": LeaveRoomSucceed,
        "CreateGame": CreateGame,
        "CreateGameSucceed": CreateGameSucceed,
        "LaunchGame": LaunchGame,
        "AddBot": AddBot,
        "BroadcastUpdateRoom": BroadcastUpdateRoom,
        "BroadcastUpdateLobby": BroadcastUpdateLobby,
        "BroadcastNewRoomToLobby": BroadcastNewRoomToLobby,
        "StatusRoom": StatusRoom,
        "NewHost": NewHost,
        "DeleteBot": DeleteBot,
        # Internal packets
        "InternalCheckPlayerValidity": InternalCheckPlayerValidity,
        "InternalPlayerDisconnect": InternalPlayerDisconnect,
        "InternalLobbyConnect": InternalLobbyConnect,
        "InternalLobbyDisconnect": InternalLobbyDisconnect
    }

    @staticmethod
    def is_packet(obj: Dict) -> bool:
        return "name" in obj

    @staticmethod
    def deserialize_packet(obj: Dict) -> "Packet":
        if not PacketUtils.is_packet(obj):
            raise PacketException("Could not deserialize packet")

        packet_name = obj.get("name")

        if packet_name not in PacketUtils.packets:
            raise PacketException("Invalid packet")

        # create a new instance
        packet = PacketUtils.packets[packet_name]()
        # deserialize missing values
        packet.deserialize(obj)

        return packet
