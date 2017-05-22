import falcon
import pytest
from falcon_autocrud.middleware import Middleware
from mock import patch, ANY
from sqlalchemy.orm import sessionmaker

from card_table import api, storage, HAND, IN_PLAY, commands
from card_table.cards import DIAMONDS, SPADES, SIX, SPADE
from card_table.storage import Facing
from test.card_table import test_db_engine, fixtures, FakeClient


@pytest.fixture()
def engine():
    test_engine = test_db_engine()
    storage.sync(test_engine)
    return test_engine


@pytest.fixture()
def app(engine):
    test_app = api.create_api([Middleware()], engine)
    return test_app


@pytest.fixture()
def with_fixtures(engine):
    sessions = sessionmaker(bind=engine)
    session = sessions()

    for model in fixtures.games:
        session.add(storage.Game(**model))

    for model in fixtures.stacks:
        session.add(storage.Stack(**model))

    for model in fixtures.cards:
        session.add(storage.Card(**model))

    for model in fixtures.commands:
        session.add(storage.Command(**model))

    session.commit()


@pytest.fixture()
def rest_api(app):
    return FakeClient(app)


class TestApiHealth(object):

    def test_get_health_ok(self, client):
        resp = client.get('/health')
        assert resp.status == falcon.HTTP_OK
        assert resp.json['title'] == falcon.HTTP_OK

    def test_get_health_failure(self, engine, client):
        from card_table.storage import Base
        Base.metadata.drop_all(engine)
        resp = client.get('/health')
        assert resp.status == falcon.HTTP_SERVICE_UNAVAILABLE
        assert resp.json['title'] == falcon.HTTP_SERVICE_UNAVAILABLE
        assert resp.json['description'] == 'Service failed health check'

    def test_put_health(self, client):
        resp = client.put('/health', {'foo': 'bar'})
        assert resp.status == falcon.HTTP_METHOD_NOT_ALLOWED

    def test_post_health(self, client):
        resp = client.post('/health', {'foo': 'bar'})
        assert resp.status == falcon.HTTP_METHOD_NOT_ALLOWED

    def test_patch_health(self, client):
        resp = client.patch('/health', {'op': 'add',
                                        'path': '/',
                                        'value': {'name': 'Alice'}})
        assert resp.status == falcon.HTTP_METHOD_NOT_ALLOWED

    def test_delete_health(self, client):
        resp = client.delete('/health')
        assert resp.status == falcon.HTTP_METHOD_NOT_ALLOWED

    def test_options_health(self, client):
        resp = client.options('/health')
        assert resp.status == falcon.HTTP_NO_CONTENT


class TestApiGame(object):
    def test_get_all(self, rest_api, with_fixtures):
        resp = rest_api.get('/games')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == len(fixtures.games)
        assert resp.json[0]['id'] == 1

    def test_get_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/games/3')

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 3
        assert resp.json['name'] == 'cancelled'
        assert resp.json['state'] == 'cancelled'

    def test_get_by_state(self, rest_api, with_fixtures):
        resp = rest_api.get('/games?state=playing')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == 1
        matched = resp.json[0]
        assert matched['id'] == 4
        assert matched['name'] == 'playing'
        assert matched['state'] == 'playing'

    def test_get_missing_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/games/80')

        assert resp.status == falcon.HTTP_NOT_FOUND

    def test_post(self, rest_api):
        data = {'name': 'new game'}
        resp = rest_api.post('/games', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['name'] == 'new game'
        assert resp.json['state'] == 'forming'

    def test_patch_by_id(self, rest_api, with_fixtures):
        data = {'name': 'deserted'}
        resp = rest_api.patch('/games/6', data)

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 6
        assert resp.json['name'] == 'deserted'

    def test_delete(self, rest_api, with_fixtures):
        deleted = rest_api.delete('/games/5')

        assert deleted.status == falcon.HTTP_NO_CONTENT

        remaining = rest_api.get('/games')
        assert remaining.status == falcon.HTTP_OK
        assert len(remaining.json) == len(fixtures.games) - 1


class TestApiStack(object):
    def test_get_all(self, rest_api, with_fixtures):
        resp = rest_api.get('/stacks')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == len(fixtures.stacks)
        assert resp.json[0]['id'] == 1

    def test_get_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/stacks/3')

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 3
        assert resp.json['owner_id'] == 100
        assert resp.json['label'] == IN_PLAY

    def test_get_by_owner_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/stacks?owner_id=100')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == 3
        assert resp.json[0]['owner_id'] == 100
        assert resp.json[1]['owner_id'] == 100
        assert resp.json[2]['owner_id'] == 100

    def test_get_missing_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/stacks/80')

        assert resp.status == falcon.HTTP_NOT_FOUND

    def test_post(self, rest_api):
        data = {'owner_id': 300, 'label': HAND}
        resp = rest_api.post('/stacks', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['owner_id'] == 300
        assert resp.json['label'] == HAND

    def test_patch_by_id(self, rest_api, with_fixtures):
        data = {"size_limit": 5}
        resp = rest_api.patch('/stacks/5', data)

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 5
        assert resp.json['owner_id'] == 200
        assert resp.json['label'] == HAND
        assert resp.json['size_limit'] == 5

    def test_delete(self, rest_api, with_fixtures):
        resp = rest_api.delete('/stacks/' + str(len(fixtures.stacks)))

        assert resp.status == falcon.HTTP_NO_CONTENT
        remaining = rest_api.get('/stacks')
        assert remaining.status == falcon.HTTP_OK
        assert len(remaining.json) == len(fixtures.stacks) - 1


class TestApiCards(object):
    def test_get_all(self, rest_api, with_fixtures):
        resp = rest_api.get('/cards')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == len(fixtures.cards)
        assert resp.json[0]['id'] == 1

    def test_get_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/cards/3')

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 3
        assert resp.json['rank_value'] == 8
        assert resp.json['suit_value'] == DIAMONDS
        assert resp.json['owner_facing'] == Facing.up.name
        assert resp.json['other_facing'] == Facing.down.name

    def test_get_by_stack_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/cards?stack_id=2&__sort=position')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == 5
        assert resp.json[0]['stack_id'] == 2
        assert resp.json[0]['position'] == 0
        assert resp.json[1]['stack_id'] == 2
        assert resp.json[1]['position'] == 1
        assert resp.json[2]['stack_id'] == 2
        assert resp.json[2]['position'] == 2

    def test_get_missing_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/cards/80')

        assert resp.status == falcon.HTTP_NOT_FOUND

    def test_post(self, rest_api):

        data = {'stack_id': 1, 'position': 2, 'suit': SPADE,
                'suit_value': SPADES, 'rank': SIX, 'rank_value': 6}
        resp = rest_api.post('/cards', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['stack_id'] == 1
        assert resp.json['position'] == 2
        assert resp.json['suit'] == SPADE
        assert resp.json['suit_value'] == SPADES
        assert resp.json['rank'] == SIX
        assert resp.json['rank_value'] == 6
        assert resp.json['owner_facing'] == Facing.down.name
        assert resp.json['other_facing'] == Facing.down.name

    def test_patch_by_id(self, rest_api, with_fixtures):
        data = {'owner_facing': 'peeking'}
        resp = rest_api.patch('/cards/1', data)

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 1
        assert resp.json['owner_facing'] == 'peeking'

    def test_delete(self, rest_api, with_fixtures):
        resp = rest_api.delete('/cards/1')

        assert resp.status == falcon.HTTP_NO_CONTENT

        remaining = rest_api.get('/cards')
        assert remaining.status == falcon.HTTP_OK
        assert len(remaining.json) == len(fixtures.cards) - 1


class TestApiCommands(object):
    def test_get_all(self, rest_api, with_fixtures):
        resp = rest_api.get('/commands')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == len(fixtures.commands)
        assert resp.json[0]['id'] == 1
        assert resp.json[0]['changes'] == {'cards': [
            {'id': 9, 'owner_facing': [Facing.down.name, Facing.up.name],
             'other_facing': [Facing.down.name, Facing.up.name]}]}

    def test_get_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/commands/3')

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 3
        assert resp.json['game_id'] == 2
        assert resp.json['actor_id'] == 700
        assert resp.json['operation'] == 'noop'
        assert resp.json['memo'] == 'nothing to see here'
        assert resp.json['changes'] == {}

    def test_get_by_game_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/commands?game_id=2')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == 3
        assert resp.json[0]['game_id'] == 2
        assert resp.json[0]['operation'] == commands.MOVE_CARDS
        assert resp.json[1]['game_id'] == 2
        assert resp.json[1]['operation'] == commands.MOVE_CARDS
        assert resp.json[2]['game_id'] == 2
        assert resp.json[2]['operation'] == commands.NOOP

    def test_get_missing_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/commands/80')

        assert resp.status == falcon.HTTP_NOT_FOUND

    @patch('card_table.commands.Operations')
    def test_post(self, operations, rest_api):
        data = {'operation': 'noop', 'game_id': 1, 'actor_id': 600,
                'changes': "{'foo': 'bar'}", 'memo': 'nothing to see here'}
        resp = rest_api.post('/commands', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['game_id'] == 1
        assert resp.json['operation'] == 'noop'
        assert resp.json['actor_id'] == 600
        assert resp.json['changes'] == {'foo': 'bar'}
        assert resp.json['memo'] == 'nothing to see here'
        assert operations.do_noop.called

    def test_patch_by_id(self, rest_api, with_fixtures):
        data = {'changes': {'foo': 'bar'}}
        resp = rest_api.patch('/commands/1', data)

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 1
        assert resp.json['changes'] == {'foo': 'bar'}

    def test_delete(self, rest_api, with_fixtures):
        resp = rest_api.delete('/commands/3')

        assert resp.status == falcon.HTTP_NO_CONTENT

        remaining = rest_api.get('/commands')
        assert remaining.status == falcon.HTTP_OK
        assert len(remaining.json) == len(fixtures.commands) - 1
