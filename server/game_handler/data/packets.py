import json
from enum import Enum

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


class GetInRoom(Packet):
    id_player: str
    id_room: str
    is_protected: bool
    password: str

    def __init__(self, id_player: str = "", id_room: str = "",
                 is_protected: bool = False, password: str = ""):
        super(GetInRoom, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.id_room = id_room
        self.is_protected = is_protected
        self.password = password

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_room = obj["id_room"]
        self.is_protected = obj["is_protected"]
        self.password = obj["password"]


class LaunchGame(Packet):
    id_player: str

    def __init__(self, id_player: str = ""):
        super(LaunchGame, self).__init__(self.__class__.__name__)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class ExceptionPacket(Packet):
    code: int

    def __init__(self, code: int = 4000):
        super(ExceptionPacket, self).__init__("Exception")
        self.code = code

    def deserialize(self, obj: object):
        self.code = int(obj["code"])


class GetInRoom(PlayerPacket):
    id_room: str
    password: str

    def __init__(self, player_token: str = ""):
        super().__init__("GetInRoom", player_token=player_token)

    def deserialize(self, obj: object):
        self.id_room = str(obj["id_room"])
        self.password = str(obj["password"])


class GetInRoomSuccess(LobbyPacket):
    def __init__(self):
        super().__init__("GetInRoom")


class LaunchGame(LobbyPacket):
    player_token: str

    def __init__(self, player_token: str = ""):
        super().__init__("LaunchGame", player_token=player_token)


class InitConnection(LobbyPacket):
    # maybe this is not useful anymore
    def __init__(self, player_token: str = ""):
        super().__init__("InitConnection", player_token=player_token)


class PingPacket(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__("Ping", player_token=player_token)


class AppletPrepare(LobbyPacket):
    def __init__(self, player_token: str = ""):
        super().__init__("AppletPrepare", player_token=player_token)


class AppletReady(PlayerPacket):
    def __init__(self, player_token: str):
        super(AppletReady, self).__init__(name=self.__class__.__name__,
                                          player_token=player_token)


class GameStart(Packet):
    """
    Contains all informations of current state
    """
    game_name: str
    options: {}
    players: []

    def __init__(self, game_name: str = "", options=None, players: [] = None):
        super(GameStart, self).__init__(self.__class__.__name__)
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
        super(PlayerDisconnect, self).__init__(self.__class__.__name__,
                                               player_token=player_token)
        self.reason = reason

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.reason = obj["reason"]


class PlayerReconnect(Packet):
    id_player: str
    reason: str

    def __init__(self, id_player: str = "", reason: str = ""):
        super(PlayerReconnect, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.reason = reason

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
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
        super(RoundStart, self).__init__(self.__class__.__name__)
        self.current_player = current_player

    def deserialize(self, obj: object):
        self.current_player = obj['current_player']


class RoundDiceThrow(Packet):
    id_player: str

    def __init__(self, id_player: str = ""):
        super(RoundDiceThrow, self).__init__(self.__class__.__name__)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class RoundDiceChoiceResult(Enum):
    ROLL_DICES = 0
    JAIL_PAY = 1
    JAIL_CARD = 2


class RoundDiceChoice(PlayerPacket):
    choice: RoundDiceChoiceResult

    def __init__(self, player_token: str = "",
                 choice: RoundDiceChoiceResult = 0):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.choice = choice

    def deserialize(self, obj: object):
        super().deserialize(obj)
        self.choice = RoundDiceChoiceResult(int(obj['choice']))


class RoundDiceResults(PlayerPacket):
    result: RoundDiceChoiceResult
    dice1: int
    dice2: int

    def __init__(self, player_token: str = "",
                 result: RoundDiceChoiceResult = 0,
                 dice1: int = 0,
                 dice2: int = 0):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)
        self.result = result
        self.dice1 = dice1
        self.dice2 = dice2


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


class RoundRandomCard(Packet):
    id_player: str
    is_communautaire: bool
    card_content: str

    def __init__(
            self, id_player: str = "", is_communautaire: bool = False,
            card_content: str = ""
    ):
        super(RoundRandomCard, self).__init__(self.__class__.__name__)
        self.id_player = id_player
        self.is_communautaire = is_communautaire
        self.card_content = card_content

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.is_communautaire = obj["is_communautaire"]
        self.card_content = obj["card_content"]


class PlayerUpdateBalance(PlayerPacket):
    id_player: str
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
        self.old_balance = obj["old_balance"]
        self.new_balance = obj["new_balance"]
        self.reason = obj["reason"]


class PlayerEnterPrison(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class PlayerExitPrison(PlayerPacket):
    def __init__(self, player_token: str = ""):
        super().__init__(name=self.__class__.__name__,
                         player_token=player_token)


class ActionExchange(Packet):
    id_player: str

    def __init__(self, id_player: str = ""):
        super(ActionExchange, self).__init__(self.__class__.__name__)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


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
        super(ActionExchangeDecline, self).__init__(self.__class__.__name__)


class ActionExchangeCounter(Packet):
    def __init__(self):
        super(ActionExchangeCounter, self).__init__(self.__class__.__name__)


class ActionExchangeCancel(Packet):
    reason: str

    def __init__(self, reason: str = ""):
        super(ActionExchangeCancel, self).__init__(self.__class__.__name__)
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
# TODO:

class CreateGame(LobbyPacket):
    # TODO: all the other options and stuff
    def __init__(self, player_token: str = ""):
        super().__init__("CreateGame", player_token=player_token)


class PacketUtils:
    packets: dict = {
        "Exception": ExceptionPacket,
        "AppletPrepare": AppletPrepare,
        "AppletReady": AppletReady,
        "PlayerDisconnect": PlayerDisconnect,
        "PlayerReconnect": PlayerReconnect,
        "GameStartDice": GameStartDice,
        "GameStartDiceThrow": GameStartDiceThrow,
        "GameStartDiceResults": GameStartDiceResults,
        "RoundStart": RoundStart,
        "RoundDiceThrow": RoundDiceThrow,
        "RoundDiceChoice": RoundDiceChoice,
        "RoundDiceResults": RoundDiceResults,
        "PlayerMove": PlayerMove,
        "RoundRandomCard": RoundRandomCard,
        "PlayerUpdateBalance": PlayerUpdateBalance,
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
        "CreateGame": CreateGame,
        # Internal packets
        "InternalCheckPlayerValidity": InternalCheckPlayerValidity,
        "InternalPlayerDisconnect": InternalPlayerDisconnect
    }

    @staticmethod
    def is_packet(obj: dict) -> bool:
        return "name" in obj

    @staticmethod
    def deserialize_packet(obj: dict) -> "Packet":
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
