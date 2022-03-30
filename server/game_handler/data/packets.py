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


class LobbyPacket(Packet):
    """
    Lobby packet => inherits Packet
    """
    pass


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


class InternalCheckPlayerValidity(InternalPacket):
    player_token: str
    valid: bool

    def __init__(self, player_token: str = "", valid: bool = False):
        super().__init__(name=self.__class__.__name__)
        self.player_token = player_token
        self.valid = valid

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.valid = bool(obj['valid'])


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


class GetInRoom(LobbyPacket):
    player_token: str
    game_token: str
    password: str

    def __init__(self, player_token: str = "", game_token: str = "",
                 password: str = ""):
        super(GetInRoom, self).__init__(self.__class__.__name__)
        self.player_token = player_token
        self.game_token = game_token
        self.password = password

    def deserialize(self, obj: object):
        self.player_token = obj["player_token"]
        self.game_token = obj["game_token"]
        self.password = obj["password"]


class LaunchGame(Packet):
    player_token: str

    def __init__(self, player_token: str = ""):
        super(LaunchGame, self).__init__(self.__class__.__name__)
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj["player_token"]


class ExceptionPacket(Packet):
    code: int

    def __init__(self, code: int = 4000):
        super().__init__("Exception")
        self.code = code

    def deserialize(self, obj: object):
        self.code = int(obj["code"])


class GetInRoomSuccess(LobbyPacket):
    piece: int

    def __init__(self, piece: int = 0):
        super().__init__("GetInRoomSuccess")
        self.piece = piece

    def deserialize(self, obj: object):
        self.piece = obj['piece']


class GetOutRoom(LobbyPacket):
    player_token: str
    game_token: str

    def __init__(self, player_token: str = "", game_token: str = ""):
        super().__init__("GetOutRoom")
        self.player_token = player_token
        self.game_token = game_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.game_token = obj['game_token']


class GetOutRoomSuccess(LobbyPacket):
    def __init__(self):
        super().__init__("GetOutRoomSuccess")


class UpdateReason(Enum):
    NEW_CONNECTION = 0
    NEW_PLAYER = 1
    PLAYER_LEFT = 2
    ROOM_DELETED = 3
    ROOM_CREATED = 4
    HOST_LEFT = 5
    LAUNCHING_GAME = 6
    NEW_BOT = 7

    @staticmethod
    def has_value(value):
        return value in set(item.value for item in UpdateReason)


class StatusRoom(LobbyPacket):
    game_token: str
    name: str
    nb_players: int
    max_nb_players: int
    players: List[str]  # list of players
    option_auction: bool
    option_double_on_start: bool
    option_max_time: int
    option_maxnb_rounds: int
    option_first_round_buy: bool
    starting_balance: int

    def __init__(self, game_token: str = "", name: str = "",
                 nb_players: int = 0, max_nb_players: int = 0,
                 players: List[str] = None, option_auction: bool = False,
                 option_double_on_start: bool = False,
                 option_max_time: int = 0, option_maxnb_rounds: int = 0,
                 option_first_round_buy: bool = False,
                 starting_balance: int = 0):
        super().__init__("StatusRoom")
        self.game_token = game_token
        self.name = name
        self.nb_players = nb_players
        self.max_nb_players = max_nb_players
        self.players = players
        self.option_auction = option_auction
        self.option_double_on_start = option_double_on_start
        self.option_max_time = option_max_time
        self.option_maxnb_rounds = option_maxnb_rounds
        self.option_first_round_buy = option_first_round_buy
        self.starting_balance = starting_balance

    def deserialize(self, obj: object):
        self.game_token = obj['game_token']
        self.name = obj['name']
        self.nb_players = obj['nb_players']
        self.max_nb_players = obj['max_nb_players']
        self.players = obj['players']
        self.option_auction = obj['option_auction']
        self.option_double_on_start = obj['option_double_on_start']
        self.option_max_time = obj['option_max_time']
        self.option_maxnb_rounds = obj['option_maxnb_rounds']
        self.option_first_round_buy = obj['option_first_round_buy']
        self.starting_balance = obj['starting_balance']


class BroadcastNewRoomToLobby(LobbyPacket):
    game_token: str
    name: str
    nb_players: int
    max_nb_players: int
    is_private: bool
    has_password: bool

    def __init__(self, game_token: str = "", name: str = "",
                 nb_players: int = 0, max_nb_players: int = 0,
                 is_private: bool = False, has_password: bool = False):
        super().__init__("BroadcastNewRoomToLobby")
        self.game_token = game_token
        self.name = name
        self.nb_players = nb_players
        self.max_nb_players = max_nb_players
        self.is_private = is_private
        self.has_password = has_password

    def deserialize(self, obj: object):
        self.game_token = obj['game_token']
        self.name = obj['name']
        self.nb_players = obj['nb_players']
        self.max_nb_players = obj['max_nb_players']
        self.is_private = obj['is_private']
        self.has_password = obj['has_password']


class BroadcastUpdateLobby(LobbyPacket):
    game_token: str
    reason: int

    def __init__(self, game_token: str = "",
                 reason: int = 0):
        super().__init__("BroadcastUpdatedRoom")
        self.game_token = game_token
        self.reason = reason

    def deserialize(self, obj: object):
        self.game_token = obj['game_token']
        self.reason = obj['reason']


class BroadcastUpdateRoom(LobbyPacket):
    game_token: str
    nb_players: int
    player: str
    reason: int

    def __init__(self, game_token: str = "", nb_players: int = 0,
                 reason: int = 0, player: str = None):
        super().__init__("BroadcastUpdatedRoom")
        self.game_token = game_token
        self.nb_players = nb_players
        self.player = player
        self.reason = reason

    def deserialize(self, obj: object):
        self.game_token = obj['game_token']
        self.nb_players = obj['nb_players']
        self.player = obj['player']
        self.reason = obj['reason']


class NewHost(LobbyPacket):
    def __init__(self):
        super().__init__("NewHost")


class PingPacket(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__("Ping", player_token=player_token)


class AppletPrepare(LobbyPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__("AppletPrepare")
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']


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

    def __init__(self, player_token: str = "", reason: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.reason = reason

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.reason = obj["reason"]


class GameStartDice(Packet):
    def __init__(self):
        super(GameStartDice, self).__init__(self.__class__.__name__)


class GameStartDiceThrow(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(self.__class__.__name__, player_token=player_token)


class GameStartDiceResults(Packet):
    dice_result: []

    def __init__(self, dice_result: [] = None):
        super(GameStartDiceResults, self).__init__(self.__class__.__name__)
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
        self.choice = int(obj['choice'])


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
        self.result = RoundDiceChoiceResult(int(obj['result']))
        self.dice1 = int(obj['dice1'])
        self.dice2 = int(obj['dice2'])


class PlayerMove(PlayerPacket):
    destination: int

    def __init__(self, player_token: str = "",
                 destination: int = 0):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.destination = destination

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.destination = obj["destination"]


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
        self.card_id = int(obj['card_id']) if 'card_id' in obj else 0
        self.is_community = bool(
            obj['is_community']) if 'is_community' in obj else False


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
        self.old_balance = obj['old_balance']
        self.new_balance = obj['new_balance']
        self.reason = obj['reason']


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
        self.amount = int(obj['amount']) if 'amount' in obj else 0
        self.reason = obj['reason']


class PlayerEnterPrison(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class PlayerExitPrison(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchange(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchangePlayerSelect(Packet):
    id_init_request: str
    id_of_requested: str
    content_trade: str

    def __init__(
            self, id_init_request: str = "", id_of_requested: str = "",
            content_trade: str = ""
    ):
        super(ActionExchangePlayerSelect, self).__init__(
            self.__class__.__name__)
        self.id_init_request = id_init_request
        self.id_of_requested = id_of_requested
        self.content_trade = content_trade

    def deserialize(self, obj: object):
        self.id_init_request = obj["id_init_request"]
        self.id_of_requested = obj["id_of_requested"]
        self.content_trade = obj["content_trade"]


class ActionExchangeTradeSelect(Packet):
    id_init_request: str
    id_of_requested: str
    content_trade: str

    def __init__(
            self, id_init_request: str = "", id_of_requested: str = "",
            content_trade: str = ""
    ):
        super(ActionExchangeTradeSelect, self).__init__(
            self.__class__.__name__)
        self.id_init_request = id_init_request
        self.id_of_requested = id_of_requested
        self.content_trade = content_trade

    def deserialize(self, obj: object):
        self.id_init_request = obj["id_init_request"]
        self.id_of_requested = obj["id_of_requested"]
        self.content_trade = obj["content_trade"]


class ActionExchangeSend(Packet):
    id_init_request: str
    id_of_requested: str
    content_trade: str

    def __init__(
            self, id_init_request: str = "", id_of_requested: str = "",
            content_trade: str = ""
    ):
        super(ActionExchangeSend, self).__init__(self.__class__.__name__)
        self.id_init_request = id_init_request
        self.id_of_requested = id_of_requested
        self.content_trade = content_trade

    def deserialize(self, obj: object):
        self.id_init_request = obj["id_init_request"]
        self.id_of_requested = obj["id_of_requested"]
        self.content_trade = obj["content_trade"]


class ActionExchangeDecline(Packet):
    def __init__(self):
        super().__init__(self.__class__.__name__)


class ActionExchangeCounter(Packet):
    def __init__(self):
        super().__init__(self.__class__.__name__)


class ActionExchangeCancel(Packet):
    reason: str

    def __init__(self, reason: str = ""):
        super().__init__(self.__class__.__name__)
        self.reason = reason

    def deserialize(self, obj: object):
        self.reason = obj["reason"]


class PlayerUpdateProperty(Packet):
    id_player: str
    is_added: bool
    property: str

    def __init__(self, id_player: str = "", is_added: bool = "",
                 property: str = ""):
        super(PlayerUpdateProperty, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.is_added = is_added
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.is_added = obj["is_added"]
        self.property = obj["property"]


class ActionAuctionProperty(Packet):
    id_player: str
    property: str
    min_price: int

    def __init__(self, id_player: str = "",
                 property: str = "", min_price: int = 0):
        super(ActionAuctionProperty, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.property = property
        self.min_price = min_price

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]
        self.min_price = obj["min_price"]


class AuctionRound(Packet):
    property: str
    id_seller: str
    current_price: int

    def __init__(self, property: str = "", id_seller: str = "",
                 curent_price: int = 0):
        super(AuctionRound, self).__init__(self.__class__.__name__)
        self.property = property
        self.id_seller = id_seller
        self.curent_price = curent_price

    def deserialize(self, obj: object):
        self.property = obj["property"]
        self.id_seller = obj["id_seller"]
        self.curent_price = obj["curent_price"]


class AuctionBid(Packet):
    property: str
    id_bidder: str
    new_price: int

    def __init__(self, id_bidder: str = "", new_price: int = 0):
        super(AuctionBid, self).__init__(self.__class__.__name__)
        self.id_bidder = id_bidder
        self.new_price = new_price

    def deserialize(self, obj: object):
        self.id_bidder = obj["id_bidder"]
        self.new_price = obj["new_price"]


class AuctionConcede(Packet):
    id_player: str

    def __init__(self, id_player: str = ""):
        super(AuctionConcede, self).__init__(self.__class__.__name__)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class AuctionEnd(Packet):
    def __init__(self):
        super(AuctionEnd, self).__init__(self.__class__.__name__)


class AuctionBuyProperty(Packet):
    id_player: str
    property: str

    def __init__(self, id_player: str = "", property: str = ""):
        super(AuctionBuyProperty, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class AuctionBuyPropertySucceed(Packet):
    id_player: str
    property: str

    def __init__(self, id_player: str = "", property: str = ""):
        super(AuctionBuyPropertySucceed, self).__init__(
            self.__class__.__name__)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionMortgageProperty(Packet):
    id_player: str
    property: str

    def __init__(self, id_player: str = "", property: str = ""):
        super(ActionMortgageProperty, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionMortgageSucceed(Packet):
    id_player: str
    property: str

    def __init__(self, id_player: str = "", property: str = ""):
        super(ActionMortgageSucceed, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionUnmortgageProperty(Packet):
    id_player: str
    property: str

    def __init__(self, id_player: str = "", property: str = ""):
        super(ActionUnmortgageProperty, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionUnmortgageSucceed(Packet):
    id_player: str
    property: str

    def __init__(self, id_player: str = "", property: str = ""):
        super(ActionUnmortgageSucceed, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionBuyHouse(Packet):
    id_player: str
    id_house: str

    def __init__(self, id_player: str = "", id_house: str = ""):
        super(ActionBuyHouse, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


class ActionBuyHouseSucceed(Packet):
    id_player: str
    id_house: str

    def __init__(self, id_player: str = "", id_house: str = ""):
        super(ActionBuyHouseSucceed, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


class ActionSellHouse(Packet):
    id_player: str
    id_house: str

    def __init__(self, id_player: str = "", id_house: str = ""):
        super(ActionSellHouse, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


class ActionSellHouseSucceed(Packet):
    id_player: str
    id_house: str

    def __init__(self, id_player: str = "", id_house: str = ""):
        super(ActionSellHouseSucceed, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


# Lobby packets

class CreateGame(LobbyPacket):
    player_token: str
    password: str
    name: str
    max_nb_players: int
    starting_balance: int
    is_private: bool
    option_auction: bool
    option_double_on_start: bool
    option_max_time: int
    option_maxnb_rounds: int
    option_first_round_buy: bool

    def __init__(self, player_token: str = "", password: str = "",
                 name: str = "", max_nb_players: int = 0,
                 is_private: bool = False, starting_balance: int = 0,
                 option_auction: bool = False,
                 option_double_on_start: bool = False,
                 option_max_time: int = 0,
                 option_maxnb_rounds: int = 0,
                 option_first_round_buy: bool = False):

        super().__init__("CreateGame")
        self.player_token = player_token
        self.password = password
        self.max_nb_players = max_nb_players
        self.is_private = is_private
        self.starting_balance = starting_balance
        self.name = name
        self.option_auction = option_auction
        self.option_double_on_start = option_double_on_start
        self.option_max_time = option_max_time
        self.option_maxnb_rounds = option_maxnb_rounds
        self.option_first_round_buy = option_first_round_buy

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.password = obj['password']
        self.max_nb_players = obj['max']
        self.is_private = obj['is_private']
        self.name = obj['name']
        self.option_auction = obj['option_auction']
        self.option_double_on_start = obj['option_double_on_start']
        self.option_max_time = obj['option_max_time']
        self.option_maxnb_rounds = obj['option_maxnb_rounds']
        self.option_first_round_buy = obj['option_first_round_buy']


class CreateGameSuccess(LobbyPacket):
    player_token: str
    piece: int

    def __init__(self, player_token: str = "", piece: int = 0):
        super().__init__("CreateGameSuccess")
        self.player_token = player_token
        self.piece = piece

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.piece = obj['piece']


class AddBot(LobbyPacket):
    player_token: str
    game_token: str
    bot_difficulty: int

    def __init__(self, player_token: str = "", game_token: str = "",
                 bot_difficulty: int = 0):
        super().__init__("AddBot")
        self.player_token = player_token
        self.game_token = game_token
        self.bot_difficulty = bot_difficulty

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.bot_difficulty = obj['bot_difficulty']
        self.game_token = obj['game_token']


class DeleteRoom(LobbyPacket):
    player_token: str
    game_token: str

    def __init__(self, player_token: str = "", game_token: str = ""):
        super().__init__("DeleteRoom")
        self.player_token = player_token
        self.game_token = game_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']
        self.game_token = obj['game_token']


class DeleteRoomSuccess(LobbyPacket):

    def __init__(self):
        super().__init__("DeleteRoomSuccess")


class InternalLobbyConnect(InternalPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__("DeleteRoomSuccess")
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']


class InternalLobbyDisconnect(InternalPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__("DeleteRoomSuccess")
        self.player_token = player_token

    def deserialize(self, obj: object):
        self.player_token = obj['player_token']


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
        "ActionExchange": ActionExchange,
        "ActionExchangePlayerSelect": ActionExchangePlayerSelect,
        "ActionExchangeTradeSelect": ActionExchangeTradeSelect,
        "ActionExchangeSend": ActionExchangeSend,
        "ActionExchangeDecline": ActionExchangeDecline,
        "ActionExchangeCounter": ActionExchangeCounter,
        "ActionExchangeCancel": ActionExchangeCancel,
        "PlayerUpdateProperty": PlayerUpdateProperty,
        "ActionAuctionProperty": ActionAuctionProperty,
        "AuctionRound": AuctionRound,
        "AuctionBid": AuctionBid,
        "AuctionConcede": AuctionConcede,
        "AuctionEnd": AuctionEnd,
        "AuctionBuyProperty": AuctionBuyProperty,
        "AuctionBuyPropertySucceed": AuctionBuyPropertySucceed,
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
        "GetInRoom": GetInRoom,
        "GetInRoomSuccess": GetInRoomSuccess,
        "GetOutRoom": GetOutRoom,
        "GetOutRoomSuccess": GetOutRoomSuccess,
        "CreateGame": CreateGame,
        "CreateGameSuccess": CreateGameSuccess,
        "LaunchGame": LaunchGame,
        "DeleteRoom": DeleteRoom,
        "DeleteRoomSuccess": DeleteRoomSuccess,
        "AddBot": AddBot,
        "BroadcastUpdateRoom": BroadcastUpdateRoom,
        "BroadcastUpdateLobby": BroadcastUpdateLobby,
        "StatusRoom": StatusRoom,
        "NewHost": NewHost,
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

        packet_name = obj["name"]

        if packet_name not in PacketUtils.packets:
            raise PacketException("Invalid packet")

        # create a new instance
        packet = PacketUtils.packets[packet_name]()
        # deserialize missing values
        packet.deserialize(obj)

        return packet
