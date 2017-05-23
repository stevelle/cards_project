import pytest
from falcon import HTTPBadRequest
from mock import patch

from card_table.commands import Operations


class TestCreateDeck(object):

    @patch('sqlalchemy.orm.Session')
    def test_deck(self, session):
        command = {'changes': {'stack_id': 1}}

        deck = Operations.do_create_deck(session, command)

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
        command = {'changes': {'stack_id': 1, 'ace': 'high'}}

        deck = Operations.do_create_deck(session, command)

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
        command = {'changes': {'stack_id': 1}}
        get.return_value = None

        with pytest.raises(HTTPBadRequest):
            Operations.do_create_deck(session, command)

    def test_deck_missing_stack_id(self):
        session = None
        command = {'changes': {}}

        with pytest.raises(HTTPBadRequest):
            Operations.do_create_deck(session, command)

    def test_deck_missing_changes(self):
        session = None
        command = {}

        with pytest.raises(HTTPBadRequest):
            Operations.do_create_deck(session, command)


class TestShuffleStack(object):

    @patch('card_table.storage.Card.find_by_stack')
    @patch('card_table.storage.Stack.get')
    @patch('card_table.commands.RANDOM')
    def test_shuffle(self, random, get, find_by_stack, session):
        cards = stub_cards()
        find_by_stack.return_value = cards
        command = {'changes': {'stack_id': 1}}
        random.randrange.side_effect = [2, 1, 0, 0]

        Operations.do_shuffle_stack(session, command)

        assert find_by_stack.called_once_with(1, session)
        assert random.randrange.call_count == len(cards)
        assert cards[2].position == 0
        assert cards[1].position == 1
        assert cards[0].position == 2
        assert cards[3].position == 3

    @patch('card_table.storage.Stack.get')
    def test_shuffle_missing_stack(self, get):
        session = None
        get.return_value = None
        command = {'changes': {}}

        with pytest.raises(HTTPBadRequest):
            Operations.do_shuffle_stack(session, command)

    def test_shuffle_missing_stack_id(self):
        session = None
        command = {'changes': {}}

        with pytest.raises(HTTPBadRequest):
            Operations.do_shuffle_stack(session, command)

    def test_shuffle_missing_changes(self):
        session = None
        command = {}

        with pytest.raises(HTTPBadRequest):
            Operations.do_shuffle_stack(session, command)


def stub_cards():
    from card_table.cards import CLUB, DIAMOND, HEART, KING, SPADE
    from card_table.storage import Card

    result_set = [Card(stack_id=1, position=0, suit=CLUB, rank=KING),
                  Card(stack_id=1, position=0, suit=DIAMOND, rank=KING),
                  Card(stack_id=1, position=0, suit=HEART, rank=KING),
                  Card(stack_id=1, position=0, suit=SPADE, rank=KING)]

    return result_set
