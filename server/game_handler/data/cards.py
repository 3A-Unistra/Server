from enum import Enum


class CardActionType(Enum):
    RECEIVE_BANK = 0
    GIVE_BANK = 1
    MOVE_FORWARD = 2
    MOVE_BACKWARD = 3
    GOTO_POSITION = 4
    GOTO_JAIL = 5
    GIVE_ALL = 6
    RECEIVE_ALL = 7
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
