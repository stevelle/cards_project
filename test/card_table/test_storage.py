from card_table import IN_PLAY
from card_table.cards import DIAMOND, EIGHT
from card_table.storage import Card, Stack


class TestCard(object):

    def test_get(self, session, with_fixtures):
        card = Card.get(3, session)
        assert card.suit == DIAMOND
        assert card.rank == EIGHT

    def test_find_by_stack(self, session, with_fixtures):
        assert len(Card.find_by_stack(1, session)) == 2
        assert len(Card.find_by_stack(2, session)) == 5
        assert len(Card.find_by_stack(4, session)) == 1

    def test_find_by_stack_missing(self, session):
        assert len(Card.find_by_stack(80, session)) == 0


class TestStack(object):

    def test_get(self, session, with_fixtures):
        assert Stack.get(3, session).label == IN_PLAY

    def test_get_missing(self, session):
        assert Stack.get(80, session) is None
