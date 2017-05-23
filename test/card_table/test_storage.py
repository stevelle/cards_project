from card_table.storage import Card


class TestCard(object):

    def test_find_by_stack(self, session, with_fixtures):
        assert len(Card.find_by_stack(1, session)) == 2
        assert len(Card.find_by_stack(2, session)) == 5
        assert len(Card.find_by_stack(4, session)) == 1

    def test_find_by_stack_missing(self, session):
        assert len(Card.find_by_stack(80, session)) == 0
