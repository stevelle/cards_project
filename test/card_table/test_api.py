import falcon
import pytest

from card_table import api


@pytest.fixture()
def app():
    test_app = api.create_api([])
    return test_app


class TestApiHealth:

    def test_get_health(self, client):
        resp = client.get('/health')
        assert resp.status == falcon.HTTP_OK
        assert resp.json['status'] == 'ok'

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
