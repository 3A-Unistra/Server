from enum import Enum
from typing import Optional


class CardActionType(Enum):
    RECEIVE_BANK = 0
    GIVE_BOARD = 1
    MOVE_BACKWARD = 2
    GOTO_POSITION = 3
    GOTO_JAIL = 4
    GIVE_ALL = 5
    RECEIVE_ALL = 6
    LEAVE_JAIL = 7
    CLOSEST_STATION = 8
    CLOSEST_COMPANY = 9
    GIVE_BOARD_HOUSES = 10

    @staticmethod
    def has_value(value):
        return value in set(item.value for item in CardActionType)


class Card:
    id_: int
    action_type: CardActionType
    action_value: int
    alt: int
    available: bool  # If a player has this card in his deck

    def __init__(self, id_: int = 0,
                 action_type: CardActionType = CardActionType.RECEIVE_BANK,
                 action_value: int = 0, alt: int = 0):
        """
        :param id_: Card ID
        :param action_type: What action this card executes when used
        :param action_value: Action's value if needed
        :param alt: Alt value for some special cards
        """
        self.id_ = id_
        self.action_type = action_type
        self.action_value = action_value
        self.alt = alt
        self.available = True

    def deserialize(self, obj: dict):
        self.id_ = int(obj['id']) if 'id' in obj else 0
        action_type = int(obj['type']) if 'type' in obj else 0

        if CardActionType.has_value(action_type):
            self.action_type = CardActionType(action_type)
        else:  # Should not happen.
            self.action_type = CardActionType.RECEIVE_BANK

        self.action_value = int(obj['value']) if 'value' in obj else 0
        self.alt = int(obj['alt']) if 'alt' in obj else 0


class ChanceCard(Card):
    pass


class CommunityCard(Card):
    pass


class CardUtils:

    @staticmethod
    def is_card(obj: dict) -> bool:
        return 'id' in obj and 'type' in obj and 'value' in obj \
               and 'group' in obj

    @staticmethod
    def load_from_json(obj: dict) -> Optional["Card"]:
        if not CardUtils.is_card(obj):
            return None

        group = int(obj['group'])

        # Create instance of card
        card = ChanceCard() if group == 0 else CommunityCard()

        # Deserialize objects
        card.deserialize(obj)

        return card
