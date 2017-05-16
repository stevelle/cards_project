import falcon
import pytest

from falcon_autocrud.middleware import Middleware
from sqlalchemy.orm import sessionmaker

from card_table import api, storage
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
    Session = sessionmaker(bind=engine)
    session = Session()
    for model in fixtures.games:
        session.add(storage.Game(**model))
    session.commit()


@pytest.fixture()
def games_api(app):
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
    def test_get_all(self, games_api, with_fixtures):
        resp = games_api.get('/games')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == len(fixtures.games)
        assert resp.json[0]['id'] == 1

    def test_get_by_id(self, games_api, with_fixtures):
        resp = games_api.get('/games/3')

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 3
        assert resp.json['name'] == 'cancelled'
        assert resp.json['state'] == 'cancelled'

    def test_get_by_state(self, games_api, with_fixtures):
        resp = games_api.get('/games?state=playing')

        assert resp.status == falcon.HTTP_OK
        assert len(resp.json) == 1
        matched = resp.json[0]
        assert matched['id'] == 4
        assert matched['name'] == 'playing'
        assert matched['state'] == 'playing'

    def test_get_missing_by_id(self, games_api, with_fixtures):
        resp = games_api.get('/games/80')

        assert resp.status == falcon.HTTP_NOT_FOUND

    def test_post(self, games_api):
        data = {'name': 'new game'}
        resp = games_api.post('/games', data)

        assert resp.status == falcon.HTTP_CREATED
        assert resp.json['id'] == 1
        assert resp.json['name'] == 'new game'
        assert resp.json['state'] == 'forming'

    def test_patch_by_id(self, games_api, with_fixtures):
        data = {"name": "deserted"}
        resp = games_api.patch('/games/6', data)

        assert resp.status == falcon.HTTP_OK
        assert resp.json['id'] == 6
        assert resp.json['name'] == 'deserted'

    def test_delete(self, games_api, with_fixtures):
        deleted = games_api.delete('/games/5')

        assert deleted.status == falcon.HTTP_NO_CONTENT

        remaining = games_api.get('/games')
        assert remaining.status == falcon.HTTP_OK
        assert len(remaining.json) == len(fixtures.games) - 1
