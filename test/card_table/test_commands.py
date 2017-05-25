import pytest
from falcon import HTTPBadRequest
from mock import patch

from card_table.commands import execute, Operations
from card_table.storage import Command, Card


class TestExecute(object):
    def test_missing_changes(self):
        session = None
        command = Command(operation='create deck')

        with pytest.raises(HTTPBadRequest):
            execute(session, command)

    def test_noop(self):
        session = None
        command = Command(operation='noop', changes='{}')

        execute(session, command)

    @patch('card_table.storage.Stack.get')
    def test_create_deck(self, stack, session):
        command = Command(operation='create deck', changes='{"stack_id": 1}')

        execute(session, command)

    @patch('card_table.storage.Stack.get')
    def test_shuffle_stack(self, stack, session):
        command = Command(operation='shuffle stack', changes='{"stack_id": 1}')

        execute(session, command)

    def test_invalid_operation(self):
        session = None
        command = Command(operation='invalid')

        with pytest.raises(HTTPBadRequest):
            execute(session, command)


class TestCreateDeck(object):

    @patch('sqlalchemy.orm.Session')
    def test_deck(self, session):
        kwargs = {'stack_id': 1}

        deck = Operations.do_create_deck(session, **kwargs)

        assert session.query.get.called_once_with(1)
        assert len(deck) == 52
        assert session.addall.called_with(deck)
        aces = [c for c in deck if c.rank == 'ace']
        assert len(aces) == 4
        assert aces[0].rank_value == 1
        kings = [c for c in deck if c.rank == 'king']
        assert len(kings) == 4
        assert kings[0].rank_value == 13

    @patch('sqlalchemy.orm.Session')
    def test_deck_ace_high(self, session):
        kwargs = {'stack_id': 1, 'ace': 'high'}

        deck = Operations.do_create_deck(session, **kwargs)

        assert session.query.get.called_once_with(1)
        assert len(deck) == 52
        assert session.addall.called_with(deck)
        twos = [c for c in deck if c.rank == '2']
        assert len(twos) == 4
        assert twos[0].rank_value == 2
        aces = [c for c in deck if c.rank == 'ace']
        assert len(aces) == 4
        assert aces[0].rank_value == 14

    @patch('sqlalchemy.orm.Session')
    @patch('card_table.storage.Stack.get')
    def test_deck_missing_stack(self, get, session):
        kwargs = {'stack_id': 80}
        get.return_value = None

        with pytest.raises(HTTPBadRequest):
            Operations.do_create_deck(session, **kwargs)

    def test_deck_missing_stack_id(self):
        session = None
        kwargs = {}

        with pytest.raises(HTTPBadRequest):
            Operations.do_create_deck(session, **kwargs)


class TestShuffleStack(object):

    @patch('card_table.storage.Card.find_by_stack')
    @patch('card_table.storage.Stack.get')
    @patch('card_table.commands.RANDOM')
    def test_shuffle(self, random, get, find_by_stack, session):
        cards = stub_cards()
        find_by_stack.return_value = cards
        kwargs = {'stack_id': 1}
        random.randrange.side_effect = [2, 1, 0, 0]

        Operations.do_shuffle_stack(session, **kwargs)

        assert find_by_stack.called_once_with(1, session)
        assert random.randrange.call_count == len(cards)
        assert cards[2].position == 0
        assert cards[1].position == 1
        assert cards[0].position == 2
        assert cards[3].position == 3

    @patch('card_table.storage.Card.find_by_stack')
    @patch('card_table.storage.Stack.get')
    @patch('card_table.commands.RANDOM')
    def test_shuffle_empty(self, random, get, find_by_stack, session):
        find_by_stack.return_value = []
        kwargs = {'stack_id': 1}
        random.randrange.side_effect = [2, 1, 0, 0]

        Operations.do_shuffle_stack(session, **kwargs)

        assert find_by_stack.called_once_with(1, session)
        assert random.randrange.call_count == 0

    @patch('card_table.storage.Stack.get')
    def test_shuffle_missing_stack(self, get):
        session = None
        get.return_value = None
        kwargs = {'stack_id': 80}

        with pytest.raises(HTTPBadRequest):
            Operations.do_shuffle_stack(session, **kwargs)

    def test_shuffle_missing_stack_id(self):
        session = None
        kwargs = {}

        with pytest.raises(HTTPBadRequest):
            Operations.do_shuffle_stack(session, **kwargs)


class TestMoveCards(object):

    def test_card_reorder(self, session, with_fixtures):
        kwargs = {"cards": [{"id": 4, "position": 4}]}

        Operations.do_move_cards(session, **kwargs)
        assert Card.get(4, session).position == 4

    def test_card_changes_stacks(self, session, with_fixtures):
        kwargs = {"cards": [{"id": 4, "stack_id": 4}]}

        Operations.do_move_cards(session, **kwargs)
        assert Card.get(4, session).stack_id == 4

    def test_missing_cards(self):
        session = None
        kwargs = {}

        with pytest.raises(HTTPBadRequest):
            Operations.do_move_cards(session, **kwargs)

    def test_empty_cards(self):
        session = None
        kwargs = {"cards": []}

        with pytest.raises(HTTPBadRequest):
            Operations.do_move_cards(session, **kwargs)

    def test_card_missing_id(self):
        session = None
        kwargs = {"cards": [{"position": 5}]}

        with pytest.raises(HTTPBadRequest):
            Operations.do_move_cards(session, **kwargs)

    @patch('card_table.storage.Card.get')
    def test_card_invalid_id(self, get):
        session = None
        kwargs = {"cards": [{"id": 80}]}
        get.return_value = None

        with pytest.raises(HTTPBadRequest):
            Operations.do_move_cards(session, **kwargs)

    def test_update_protected_property(self, session, with_fixtures):
        kwargs = {"cards": [{"id": 4, "updated_at": "2016-09-14T14:25:47Z"}]}

        with pytest.raises(HTTPBadRequest):
            Operations.do_move_cards(session, **kwargs)

    def test_card_changes_stack_invalid(self, session, with_fixtures):
        kwargs = {"cards": [{"id": 4, "stack_id": 80}]}

        with pytest.raises(HTTPBadRequest):
            Operations.do_move_cards(session, **kwargs)


def stub_cards():
    from card_table.cards import CLUB, DIAMOND, HEART, KING, SPADE
    from card_table.storage import Card

    result_set = [Card(stack_id=1, position=0, suit=CLUB, rank=KING),
                  Card(stack_id=1, position=0, suit=DIAMOND, rank=KING),
                  Card(stack_id=1, position=0, suit=HEART, rank=KING),
                  Card(stack_id=1, position=0, suit=SPADE, rank=KING)]

    return result_set
