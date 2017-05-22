import falcon

MAKE_STACK = 'make stack'
MOVE_CARDS = 'move cards'
NOOP = 'noop'

COMMANDS = [MAKE_STACK, MOVE_CARDS, NOOP]


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
    def do_make_stack(db_session, command):
        """ Make one new card stack

        :param db_session: db session to use
        :param command: the command to perform
        """
        # TODO Implementation
        pass

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
