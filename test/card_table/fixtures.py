from card_table import storage

games = [{'name': 'forming', 'state': storage.GameState.forming},
         {'name': 'starting', 'state': storage.GameState.starting},
         {'name': 'cancelled', 'state': storage.GameState.cancelled},
         {'name': 'playing', 'state': storage.GameState.playing},
         {'name': 'paused', 'state': storage.GameState.paused},
         {'name': 'abandoned', 'state': storage.GameState.abandoned},
         {'name': 'finished', 'state': storage.GameState.finished},
         ]
