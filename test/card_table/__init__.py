import json
from urllib.parse import urlparse, urlencode

from falcon import testing
from sqlalchemy import create_engine

from card_table import storage


def test_db_engine():
    engine = create_engine("sqlite:///:memory:")
    storage.sync(engine)
    return engine


class FakeClient(object):
    def __init__(self, app):
        self.app = app

    def get(self, path, headers=None):
        return self.__fake_request(path, 'GET', headers=headers)

    def head(self, path, headers=None):
        return self.__fake_request(path, 'HEAD', headers=headers)

    def options(self, path, headers=None):
        return self.__fake_request(path, 'OPTIONS', headers=headers)

    def post(self, path, data, headers=None):
        return self.__fake_request(path, 'POST', data, headers=headers)

    def patch(self, path, data, headers=None):
        return self.__fake_request(path, 'PATCH', data, headers=headers)

    def put(self, path, data, headers=None):
        return self.__fake_request(path, 'PUT', data, headers=headers)

    def delete(self, path, headers=None):
        return self.__fake_request(path, 'DELETE', headers=headers)

    def __fake_request(self, path, method, data=None, headers=None):
        kwargs = {'method': method, 'body': json.dumps(data),
                  'headers': self.__fake_headers(headers)}

        parsed = urlparse(path)
        path = parsed.path
        if parsed.query:
            kwargs['query_string'] = parsed.query
        if isinstance(kwargs.get('query_string', None), dict):
            kwargs['query_string'] = urlencode(kwargs['query_string'])

        env = testing.create_environ(path=path, **kwargs)

        resp = testing.StartResponseMock()
        resp.environ = env
        body = self.app(env, resp)

        resp.headers = resp.headers_dict
        resp.status_code = int(resp.status.split(' ')[0])
        resp.body = b''.join(list(body)) if body else b''
        if body:
            resp.body = resp.body.decode()
            resp.json = json.loads(resp.body)['data']
        return resp

    @staticmethod
    def __fake_headers(headers):
        json_headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json'}
        if headers:
            json_headers.update(headers)
        headers = json_headers
        return headers
