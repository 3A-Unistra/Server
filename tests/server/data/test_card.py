from unittest import TestCase

from server.game_handler.data import Card
from server.game_handler.data.cards import CardActionType, CommunityCard, \
    ChanceCard


class TestCard(TestCase):

    def setUp(self):
        pass

    def test_card(self):
        card = Card(id_=1,
                    action_type=CardActionType.LEAVE_JAIL,
                    action_value=0)

        assert card.id_ == 1
        assert card.action_type == CardActionType.LEAVE_JAIL
        assert card.action_value == 0

    def test_community_card(self):
        card = CommunityCard(id_=1,
                             action_type=CardActionType.LEAVE_JAIL,
                             action_value=0)

        assert isinstance(card, CommunityCard)
        assert isinstance(card, Card)
        assert card.id_ == 1
        assert card.action_type == CardActionType.LEAVE_JAIL
        assert card.action_value == 0

    def test_chance_card(self):
        card = ChanceCard(id_=1,
                          action_type=CardActionType.LEAVE_JAIL,
                          action_value=0)

        assert isinstance(card, ChanceCard)
        assert isinstance(card, Card)
        assert card.id_ == 1
        assert card.action_type == CardActionType.LEAVE_JAIL
        assert card.action_value == 0
