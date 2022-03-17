from enum import Enum


class CardActionType(Enum):
    ADD_BALANCE = 0
    MOVE_FORWARD = 1
    MOVE_BACKWARD = 2
    GOTO_POSITION = 3
    GOTO_JAIL = 4
    GIVE_ALL = 5
    RECEIVE_ALL = 6
    GIVE_BANK = 7
    LEAVE_JAIL = 8


class Card:
    id_: int
    action_type: CardActionType
    action_value: int
    available: bool  # If a player has this card in his deck

    def __init__(self, id_: int, action_type: CardActionType,
                 action_value: int = 0):
        """
        :param id_: Card ID
        :param action_type: What action this card executes when used
        :param action_value: Action's value if needed
        """
        self.id_ = id_
        self.action_type = action_type
        self.action_value = action_value
        self.available = True


class ChanceCard(Card):
    pass


class CommunityCard(Card):
    pass
