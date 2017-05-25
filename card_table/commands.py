import json
import random

import falcon

import card_table.cards as cards
from card_table.storage import Card, Stack

RANDOM = random.SystemRandom()

CREATE_DECK = 'create deck'
MOVE_CARDS = 'move cards'
NOOP = 'noop'
SHUFFLE_STACK = 'shuffle stack'

COMMANDS = [CREATE_DECK, MOVE_CARDS, NOOP, SHUFFLE_STACK]


def execute(db_session, resource):
    if resource.operation in COMMANDS:
        f_name = 'do_' + resource.operation.replace(' ', '_')

        func = getattr(Operations, f_name, None)
        if func:
            kwargs = __get_kwargs(resource)
            return func(db_session, **kwargs)

    raise falcon.HTTPInvalidParam(msg=resource.operation,
                                  param_name='operation')


class Operations(object):

    @staticmethod
    def do_create_deck(db_session, **kwargs):
        """ Create a standard deck of cards

        The resulting deck is ordered consistently, ascending, by suit.

        The command MUST contain (key, value): ('changes', dict())
        The kwargs MUST contain (key, value): ('stack_id', {integer}) where
            {integer} is an existing stack to place the cards into
        The changed dict MAY contain (key, value):
            ('ace': ['high', 'low']) to indicate the value of an ace in play
            DEFAULT: ace is low

        :param db_session: db session to use
        :param kwargs: the command to perform
        :return a new deck of cards
        """
        stack_id = Operations.__require_stack_id(db_session, **kwargs)

        # default ace low
        ranks = cards.COMMON_RANKS_ACE_LOW
        if 'ace' in kwargs:
            if kwargs['ace'] == 'high':
                ranks = cards.COMMON_RANKS_ACE_HIGH

        deck = []
        for suit, suit_value in cards.COMMON_SUITS.items():
            for rank, rank_value in ranks.items():
                card = Card(stack_id=stack_id, position=len(deck), suit=suit,
                            suit_value=suit_value, rank=rank,
                            rank_value=rank_value)
                deck.append(card)
        db_session.add_all(deck)
        return deck

    @staticmethod
    def do_move_cards(db_session, **kwargs):
        """ Move one or more cards in some way

        :param db_session: db session to use
        :param kwargs: the command to perform
        """
        update_sets = _require_param('cards', kwargs)
        for props in update_sets:
            _require_record('id', props, db_session, Card)

            # ensure no immutable props included in props, should contain 'id'
            protected_props = [p.key for p in Card.protected_properties()
                               if p.key != 'id']
            intersecting = set(props.keys()) & set(protected_props)
            if intersecting:
                raise falcon.HTTPInvalidParam(msg="One or more properties are "
                                                  "not modifiable.",
                                              param_name=intersecting)

            db_session.merge(Card(**props))

    @staticmethod
    def do_noop(db_session, **kwargs):
        """ Perform a No-Op

        :param db_session: ignored
        :param kwargs: all args are ignored
        """
        # No-op
        pass

    @staticmethod
    def do_shuffle_stack(db_session, **kwargs):
        """ Shuffle cards in a stack

        :param db_session: db session to use
        :param kwargs: the command to perform
        """
        stack_id = Operations.__require_stack_id(db_session, **kwargs)
        # use a copy of the found cards, for safety, testability
        card_list = list(Card.find_by_stack(stack_id, db_session))
        shuffled = 0

        while card_list:
            index = RANDOM.randrange(start=0, stop=len(card_list))
            selected = card_list.pop(index)
            selected.position = shuffled
            db_session.add(selected)
            shuffled += 1
        # not returning the shuffled stack to prevent leaking secrets

    @staticmethod
    def __require_stack_id(db_session, **kwargs):
        try:
            stack_id = kwargs['stack_id']
        except KeyError:
            raise falcon.HTTPMissingParam(param_name='stack_id')

        found_stack = Stack.get(stack_id, db_session)
        if not found_stack:
            raise falcon.HTTPInvalidParam(msg=stack_id, param_name='stack_id')

        return stack_id


def _require_param(named, data_dict):
    if named not in data_dict.keys():
        raise falcon.HTTPMissingParam(param_name=named)

    result = data_dict[named]
    if not result:
        raise falcon.HTTPInvalidParam(msg=result,
                                      param_name=named)
    return result


def _require_record(named, data_dict, session, accessor):
    record_id = _require_param(named, data_dict)

    record = accessor.get(record_id, session)
    if not record:
        raise falcon.HTTPInvalidParam(msg=record_id,
                                      param_name=named)

    return record


def __get_kwargs(command):
    try:
        changes = command.changes
        if changes:
            return json.loads(changes)

        raise falcon.HTTPMissingParam(param_name='changes')
    except ValueError:
        raise falcon.HTTPInvalidParam(msg='', param_name='changes')
