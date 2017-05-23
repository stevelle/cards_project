import random

import falcon

import card_table.cards as cards
from card_table.storage import Card

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
            return func(db_session, resource)

    raise falcon.HTTPInvalidParam(msg=resource.operation,
                                  param_name='operation')


class Operations(object):

    @staticmethod
    def do_create_deck(db_session, command):
        """ Create a standard deck of cards

        The resulting deck is ordered consistently, ascending, by suit.

        The command MUST contain (key, value): ('changes', dict())
        The changes dict MUST contain (key, value): ('stack_id', {integer})
            where {integer} is an existing stack to place the cards into
        The changed dict MAY contain (key, value):
            ('ace': ['high', 'low']) to indicate the value of an ace in play
            DEFAULT: ace is low

        :param db_session: db session to use
        :param command: the command to perform
        :return a new deck of cards
        """
        changes = Operations.__get_required_changes(command)
        stack_id = Operations.__get_required_stack_id(changes)

        # default ace low
        ranks = cards.COMMON_RANKS_ACE_LOW
        if 'ace' in changes:
            if changes['ace'] == 'high':
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
    def do_move_cards(db_session, command):
        """ Move one or more cards in some way

        :param db_session: db session to use
        :param command: the command to perform
        """
        # TODO Implementation
        pass

    @staticmethod
    def do_noop(**kwargs):
        """ Perform a No-Op

        :param kwargs: all args are ignored
        """
        # No-op
        pass

    @staticmethod
    def do_shuffle_stack(db_session, command):
        """ Shuffle cards in a stack

        :param db_session: db session to use
        :param command: the command to perform
        """
        stack_id = Operations.__get_required_stack_id(command=command)
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
    def __get_required_stack_id(changes=None, command=None):
        if changes is None:
            changes = Operations.__get_required_changes(command)
        try:
            stack_id = changes['stack_id']
        except KeyError:
            raise falcon.HTTPMissingParam(param_name='stack_id')

        # TODO validate the stack_id
        return stack_id

    @staticmethod
    def __get_required_changes(command):
        try:
            changes = command['changes']
        except KeyError:
            raise falcon.HTTPMissingParam(param_name='changes')
        return changes
