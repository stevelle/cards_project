from card_table import storage, HAND, DRAW_PILE, DISCARDS, IN_PLAY
from card_table.cards import ACE, EIGHT, FOUR, JACK, NINE, QUEEN, TEN
from card_table.cards import DIAMONDS, HEARTS, SPADES
from card_table.storage import Facing

games = [{'name': 'forming', 'state': storage.GameState.forming},
         {'name': 'starting', 'state': storage.GameState.starting},
         {'name': 'cancelled', 'state': storage.GameState.cancelled},
         {'name': 'playing', 'state': storage.GameState.playing},
         {'name': 'paused', 'state': storage.GameState.paused},
         {'name': 'abandoned', 'state': storage.GameState.abandoned},
         {'name': 'finished', 'state': storage.GameState.finished},
         ]

stacks = [{'game_id': 4, 'owner_id': 0, 'label': DRAW_PILE},
          {'game_id': 4, 'owner_id': 100, 'label': HAND},
          {'game_id': 4, 'owner_id': 100, 'label': IN_PLAY},
          {'game_id': 4, 'owner_id': 100, 'label': DISCARDS},
          {'game_id': 4, 'owner_id': 200, 'label': HAND},
          {'game_id': 4, 'owner_id': 200, 'label': IN_PLAY},
          {'game_id': 4, 'owner_id': 200, 'label': DISCARDS},
          ]

cards = [{'stack_id': 1, 'position': 0, 'suit': '♠', 'suit_value': SPADES,
          'rank': QUEEN, 'rank_value': 12},
         {'stack_id': 1, 'position': 1, 'suit': '♠', 'suit_value': HEARTS,
          'rank': QUEEN, 'rank_value': 12},
         {'stack_id': 2, 'position': 0, 'suit': '♢', 'suit_value': DIAMONDS,
          'rank': EIGHT, 'rank_value': 8, 'owner_facing': Facing.up},
         {'stack_id': 2, 'position': 1, 'suit': '♢', 'suit_value': DIAMONDS,
          'rank': ACE, 'rank_value': 14, 'owner_facing': Facing.up},
         {'stack_id': 2, 'position': 2, 'suit': '♢', 'suit_value': DIAMONDS,
          'rank': JACK, 'rank_value': 11, 'owner_facing': Facing.up},
         {'stack_id': 2, 'position': 3, 'suit': '♠', 'suit_value': SPADES,
          'rank': TEN, 'rank_value': 10, 'owner_facing': Facing.up},
         {'stack_id': 2, 'position': 4, 'suit': '♠', 'suit_value': SPADES,
          'rank': NINE, 'rank_value': 9, 'owner_facing': Facing.up},
         {'stack_id': 4, 'position': 0, 'suit': '♡', 'suit_value': HEARTS,
          'rank': FOUR, 'rank_value': 4, 'owner_facing': Facing.up,
          'other_facing': Facing.up},
         ]
