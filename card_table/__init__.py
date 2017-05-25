import logging

# PoC: debug logging
import falcon

log_level = logging.DEBUG

logging.basicConfig(
    format='[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S +0000', level=log_level)


# Convenience for use with storage.Stack.label
HAND = 'hand'
IN_PLAY = 'in play'
DRAW_PILE = 'draw pile'
DISCARDS = 'discards'
COMMON_STACKS = [HAND, IN_PLAY, DRAW_PILE, DISCARDS]


def validate_properties(clasz, props, exceptions=None, allow_immutables=False):
    if not exceptions:
        exceptions = []

    forbiddens = clasz.protected_properties()
    if not allow_immutables:
        forbiddens += clasz.immutable_properties()

    # ensure no immutable props included in props, should contain 'id'
    guarded_props = [p.key for p in forbiddens if p.key not in exceptions]
    intersecting = set(props.keys()) & set(guarded_props)
    if intersecting:
        raise falcon.HTTPInvalidParam(msg="One or more properties are not "
                                          "modifiable.",
                                      param_name=repr(intersecting))
