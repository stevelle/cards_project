import falcon
import pytest
from falcon_autocrud.middleware import Middleware
from sqlalchemy.orm import sessionmaker

from card_table import api, storage, HAND, IN_PLAY
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
                                        "path": "/",
                                        "value": {"name": "Alice"}})
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
        data = {"name": "deserted"}
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

