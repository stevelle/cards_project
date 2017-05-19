from card_table import storage, HAND, DRAW_PILE, DISCARDS, IN_PLAY

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
