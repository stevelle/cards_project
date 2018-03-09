import falcon
import pytest
from mock import patch
from tests.unit.card_table import FakeClient

import tests.unit.card_table.fixtures as fixtures
from card_table import api, HAND, IN_PLAY
from card_table.cards import DIAMONDS, SPADES, SIX, SPADE
from card_table.commands import MOVE_CARDS, NOOP
from card_table.storage import Facing


@pytest.fixture()
def app(middleware, engine):
    test_app = api.create_api(middleware, engine)
    return test_app


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

    def test_patch_id_forbidden(self, rest_api, with_fixtures):
        data = {"id": '80'}
        resp = rest_api.patch('/games/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_created_at_forbidden(self, rest_api, with_fixtures):
        data = {"created_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/games/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_updated_at_forbidden(self, rest_api, with_fixtures):
        data = {"updated_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/games/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body


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

    def test_post(self, rest_api, with_fixtures):
        data = {'owner_id': 300, 'label': HAND, 'game_id': 1}

        resp = rest_api.post('/stacks', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == len(fixtures.stacks) + 1
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

    def test_patch_id_forbidden(self, rest_api, with_fixtures):
        data = {"id": '80'}
        resp = rest_api.patch('/stacks/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_game_id_forbidden(self, rest_api, with_fixtures):
        data = {"game_id": 5}
        resp = rest_api.patch('/stacks/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_created_at_forbidden(self, rest_api, with_fixtures):
        data = {"created_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/stacks/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_updated_at_forbidden(self, rest_api, with_fixtures):
        data = {"updated_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/stacks/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_post_missing_game_id(self, rest_api, with_fixtures):
        data = {'owner_id': 300, 'label': HAND}

        resp = rest_api.post('/stacks', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'Missing' in resp.body

    def test_post_invalid_game_id(self, rest_api, with_fixtures):
        data = {'owner_id': 300, 'label': HAND, 'game_id': 80}

        resp = rest_api.post('/stacks', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'Invalid' in resp.body


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

    def test_post(self, rest_api, with_fixtures):
        data = {'stack_id': 1, 'position': 2, 'suit': SPADE,
                'suit_value': SPADES, 'rank': SIX, 'rank_value': 6}

        resp = rest_api.post('/cards', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == len(fixtures.cards) + 1
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

    def test_patch_id_forbidden(self, rest_api, with_fixtures):
        data = {"id": '80'}
        resp = rest_api.patch('/cards/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_created_at_forbidden(self, rest_api, with_fixtures):
        data = {"created_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/cards/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_updated_at_forbidden(self, rest_api, with_fixtures):
        data = {"updated_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/cards/5', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_post_missing_stack(self, rest_api):
        # no fixtures, so no stacks exist
        data = {'position': 2, 'suit': SPADE,
                'suit_value': SPADES, 'rank': SIX, 'rank_value': 6}
        resp = rest_api.post('/cards', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'Missing' in resp.body

    def test_post_invalid_stack(self, rest_api):
        # no fixtures, so no stacks exist
        data = {'stack_id': 1, 'position': 2, 'suit': SPADE,
                'suit_value': SPADES, 'rank': SIX, 'rank_value': 6}
        resp = rest_api.post('/cards', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'Invalid' in resp.body


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
        assert resp.json[0]['operation'] == MOVE_CARDS
        assert resp.json[1]['game_id'] == 2
        assert resp.json[1]['operation'] == MOVE_CARDS
        assert resp.json[2]['game_id'] == 2
        assert resp.json[2]['operation'] == NOOP

    def test_get_missing_by_id(self, rest_api, with_fixtures):
        resp = rest_api.get('/commands/80')

        assert resp.status == falcon.HTTP_NOT_FOUND

    @patch('card_table.commands.Operations')
    def test_post_noop(self, operations, rest_api):
        data = {'operation': 'noop', 'game_id': 1, 'actor_id': 600,
                'changes': '{"foo": "bar"}', 'memo': 'nothing to see here'}
        resp = rest_api.post('/commands', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['game_id'] == 1
        assert resp.json['operation'] == 'noop'
        assert resp.json['actor_id'] == 600
        assert resp.json['changes'] == {'foo': 'bar'}
        assert resp.json['memo'] == 'nothing to see here'
        assert operations.do_noop.called

    @patch('card_table.commands.Operations')
    def test_post_create_deck(self, operations, rest_api):
        data = {'operation': 'create deck', 'game_id': 1, 'actor_id': 600,
                'changes': '{"stack_id": 10}', 'memo': 'new deck'}
        resp = rest_api.post('/commands', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['game_id'] == 1
        assert resp.json['operation'] == 'create deck'
        assert resp.json['actor_id'] == 600
        assert resp.json['changes'] == {'stack_id': 10}
        assert resp.json['memo'] == 'new deck'

        expected_dict = {'stack_id': 10}
        assert operations.do_create_deck.called_once_with(expected_dict)

    @patch('card_table.commands.Operations')
    def test_post_missing_changes(self, operations, rest_api):
        data = {'operation': 'noop', 'game_id': 1, 'actor_id': 600,
                'memo': 'new deck'}

        resp = rest_api.post('/commands', data)
        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'Missing' in resp.body

    @patch('card_table.commands.Operations')
    def test_post_invalid_embedded_json(self, operations, rest_api):
        data = {'operation': 'noop', 'game_id': 1, 'actor_id': 600,
                'changes': '{invalid json', 'memo': 'new deck'}

        resp = rest_api.post('/commands', data)
        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'Invalid' in resp.body

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

    def test_patch_id_forbidden(self, rest_api, with_fixtures):
        data = {"id": '80'}
        resp = rest_api.patch('/commands/3', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_game_id_forbidden(self, rest_api, with_fixtures):
        data = {"game_id": 5}
        resp = rest_api.patch('/commands/3', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_actor_id_forbidden(self, rest_api, with_fixtures):
        data = {"actor_id": 503}
        resp = rest_api.patch('/commands/3', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_created_at_forbidden(self, rest_api, with_fixtures):
        data = {"created_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/commands/3', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body

    def test_patch_updated_at_forbidden(self, rest_api, with_fixtures):
        data = {"updated_at": '2016-8-15T09:45:52Z'}
        resp = rest_api.patch('/commands/3', data)

        assert resp.status == falcon.HTTP_BAD_REQUEST
        assert 'not modifiable' in resp.body
