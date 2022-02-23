from packet import Packet


class AppletPrepare(Packet):
    def __init__(self, name: str):
        super(AppletPrepare, self).__init__(name)


class AppletReady(Packet):
    def __init__(self, name: str):
        super(AppletReady, self).__init__(name)


class GameStart(Packet):
    def __init__(self, name: str):
        super(GameStart, self).__init__(name)


class PlayerDisconnect(Packet):
    def __init__(self, name: str, id_player: str, reason: str):
        super(PlayerDisconnect, self).__init__(name)
        self.id_player = id_player
        self.reason = reason

    def deserialize(self, obj: object):
        self.id_player = str(obj["id_player"])
        self.reason = str(obj["reason"])


class PlayerReconnect(Packet):
    def __init__(self, name: str, id_player: str, reason: str):
        super(PlayerReconnect, self).__init__(name)
        self.id_player = id_player
        self.reason = reason

    def deserialize(self, obj: object):
        self.id_player = str(obj["id_player"])
        self.reason = str(obj["reason"])


class GameStartDice(Packet):
    def __init__(self, name: str):
        super(GameStartDice, self).__init__(name)


class GameStartDiceThrow(Packet):
    def __init__(self, name: str, id_player: str):
        super(GameStartDiceThrow, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = str(obj["id_player"])


class GameStartDiceResults(Packet):
    def __init__(self, name: str, id_player: str, dice_result: int):
        super(GameStartDiceResults, self).__init__(name)
        self.id_player = id_player
        self.dice_result = dice_result

    def deserialize(self, obj: object):
        self.id_player = str(obj["id_player"])
        self.dice_result = int(obj["reason"])


class RoundStart(Packet):
    def __init__(self, name: str):
        super(RoundStart, self).__init__(name)


class RoundDiceThrow(Packet):
    def __init__(self, name: str, id_player: str):
        super(RoundDiceThrow, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = str(obj["id_player"])


class RoundDiceChoice(Packet):
    def __init__(self, name: str, id_player: str):
        super(RoundDiceChoice, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = str(obj["id_player"])


class PlayerMove(Packet):
    def __init__(self, name: str, id_moving_player: str,
                 destination_case: int):
        super(PlayerMove, self).__init__(name)
        self.id_moving_player = id_moving_player
        self.destination_case = destination_case

    def deserialize(self, obj: object):
        self.id_moving_player = str(obj["id_moving_player"])
        self.destination_case = int(obj["destination_case"])


class RoundRandomCard(Packet):
    def __init__(
        self, name: str, id_player: str, is_communautaire: bool,
        card_content: str
    ):
        super(RoundRandomCard, self).__init__(name)
        self.id_player = id_player
        self.is_communautaire = is_communautaire
        self.card_content = card_content

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.is_communautaire = obj["is_communautaire"]
        self.card_content = obj["card_content"]


class PlayerUpdateBalance(Packet):
    def __init__(
        self, name: str, id_player: str, old_balance: int, new_balance: int,
        reason: str
    ):
        super(PlayerUpdateBalance, self).__init__(name)
        self.id_player = id_player
        self.old_balance = old_balance
        self.new_balance = new_balance
        self.reason = reason

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.old_balance = obj["old_balance"]
        self.new_balance = obj["new_balance"]
        self.reason = obj["reason"]


class PlayerEnterPrison(Packet):
    def __init__(self, name: str, id_player: str):
        super(PlayerEnterPrison, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class PlayerExitPrison(Packet):
    def __init__(self, name: str, id_player: str):
        super(PlayerExitPrison, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class ActionExchange(Packet):
    def __init__(self, name: str, id_player: str):
        super(ActionExchange, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class ActionExchangePlayerSelect(Packet):
    def __init__(
        self, name: str, id_init_request: str, id_of_requested: str,
        content_trade: str
    ):
        super(ActionExchangePlayerSelect, self).__init__(name)
        self.id_init_request = id_init_request
        self.id_of_requested = id_of_requested
        self.content_trade = content_trade

    def deserialize(self, obj: object):
        self.id_init_request = obj["id_init_request"]
        self.id_of_requested = obj["id_of_requested"]
        self.content_trade = obj["content_trade"]


class ActionExchangeTradeSelect(Packet):
    def __init__(
        self, name: str, id_init_request: str, id_of_requested: str,
        content_trade: str
    ):
        super(ActionExchangeTradeSelect, self).__init__(name)
        self.id_init_request = id_init_request
        self.id_of_requested = id_of_requested
        self.content_trade = content_trade

    def deserialize(self, obj: object):
        self.id_init_request = obj["id_init_request"]
        self.id_of_requested = obj["id_of_requested"]
        self.content_trade = obj["content_trade"]


class ActionExchangeSend(Packet):
    def __init__(
        self, name: str, id_init_request: str, id_of_requested: str,
        content_trade: str
    ):
        super(ActionExchangeSend, self).__init__(name)
        self.id_init_request = id_init_request
        self.id_of_requested = id_of_requested
        self.content_trade = content_trade

    def deserialize(self, obj: object):
        self.id_init_request = obj["id_init_request"]
        self.id_of_requested = obj["id_of_requested"]
        self.content_trade = obj["content_trade"]


class ActionExchangeDecline(Packet):
    def __init__(self, name: str):
        super(ActionExchangeDecline, self).__init__(name)


class ActionExchangeCounter(Packet):
    def __init__(self, name: str):
        super(ActionExchangeCounter, self).__init__(name)


class ActionExchangeCancel(Packet):
    def __init__(self, name: str, reason: str):
        super(ActionExchangeCancel, self).__init__(name)
        self.reason = reason

    def deserialize(self, obj: object):
        self.reason = obj["reason"]


class PlayerUpdateProperty(Packet):
    def __init__(self, name: str, id_player: str, is_added: bool,
                 property: str):
        super(PlayerUpdateProperty, self).__init__(name)
        self.id_player = id_player
        self.is_added = is_added
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.is_added = obj["is_added"]
        self.property = obj["property"]


class ActionAuctionProperty(Packet):
    def __init__(self, name: str, id_player: str,
                 property: str, min_price: int):
        super(ActionAuctionProperty, self).__init__(name)
        self.id_player = id_player
        self.property = property
        self.min_price = min_price

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]
        self.min_price = obj["min_price"]


class AuctionRound(Packet):
    def __init__(self, name: str, property: str, id_seller: str,
                 curent_price: int):
        super(AuctionRound, self).__init__(name)
        self.property = property
        self.id_seller = id_seller
        self.curent_price = curent_price

    def deserialize(self, obj: object):
        self.property = obj["property"]
        self.id_seller = obj["id_seller"]
        self.curent_price = obj["curent_price"]


class AuctionBid(Packet):
    def __init__(self, name: str, id_bidder: str, new_price: int):
        super(AuctionBid, self).__init__(name)
        self.id_bidder = id_bidder
        self.new_price = new_price

    def deserialize(self, obj: object):
        self.id_bidder = obj["id_bidder"]
        self.new_price = obj["new_price"]


class AuctionConcede(Packet):
    def __init__(self, name: str, id_player: str):
        super(AuctionConcede, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]


class AuctionEnd(Packet):
    def __init__(self, name: str):
        super(AuctionEnd, self).__init__(name)


class AuctionBuyProperty(Packet):
    def __init__(self, name: str, id_player: str, property: str):
        super(AuctionBuyProperty, self).__init__(name)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class AuctionBuyPropertySucceed(Packet):
    def __init__(self, name: str, id_player: str, property: str):
        super(AuctionBuyPropertySucceed, self).__init__(name)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionMortgageProperty(Packet):
    def __init__(self, name: str, id_player: str, property: str):
        super(ActionMortgageProperty, self).__init__(name)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionMortgageSucceed(Packet):
    def __init__(self, name: str, id_player: str, property: str):
        super(ActionMortgageSucceed, self).__init__(name)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionUnmortgageProperty(Packet):
    def __init__(self, name: str, id_player: str, property: str):
        super(ActionUnmortgageProperty, self).__init__(name)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionUnmortgageSucceed(Packet):
    def __init__(self, name: str, id_player: str, property: str):
        super(ActionUnmortgageSucceed, self).__init__(name)
        self.id_player = id_player
        self.property = property

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.property = obj["property"]


class ActionBuyHouse(Packet):
    def __init__(self, name: str, id_player: str, id_house: str):
        super(ActionBuyHouse, self).__init__(name)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


class ActionBuyHouseSucceed(Packet):
    def __init__(self, name: str, id_player: str, id_house: str):
        super(ActionBuyHouseSucceed, self).__init__(name)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


class ActionSellHouse(Packet):
    def __init__(self, name: str, id_player: str, id_house: str):
        super(ActionSellHouse, self).__init__(name)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]


class ActionSellHouseSucceed(Packet):
    def __init__(self, name: str, id_player: str, id_house: str):
        super(ActionSellHouseSucceed, self).__init__(name)
        self.id_player = id_player
        self.id_house = id_house

    def deserialize(self, obj: object):
        self.id_player = obj["id_player"]
        self.id_house = obj["id_house"]
