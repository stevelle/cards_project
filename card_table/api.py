import json

import falcon

from falcon_autocrud.resource import CollectionResource, SingleResource
from sqlalchemy import bindparam, select

from card_table.storage import Game


def create_api(middleware, db_engine):
    app = falcon.API(middleware=middleware)
    app.add_route('/health', HealthResource(db_engine))
    app.add_route('/games', GameCollectionResource(db_engine))
    app.add_route('/games/{id}', GameResource(db_engine))
    return app


class HealthResource(object):

    statement = select([Game.__table__]).where(Game.id == bindparam('id'))
    error_txt = 'Service failed health check'
    ok_txt = json.dumps({'title': '200 OK',
                         'description': 'Service passed health check'})

    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.compiled_cache = {}

    def on_get(self, req, resp):
        # PoC: always OK
        if self.is_db_available():
            resp.status = falcon.HTTP_200
            resp.body = self.ok_txt
        else:
            raise falcon.HTTPServiceUnavailable(description=self.error_txt,
                                                retry_after=60)

    def is_db_available(self):
        func = self.db_engine.connect
        cache = self.compiled_cache
        try:
            with (func().execution_options(compiled_cache=cache)) as conn:
                conn.execute(self.statement, id=1).first()
            return True

        except Exception:
            return False


class GameCollectionResource(CollectionResource):
    model = Game

    @staticmethod
    def after_post(req, resp, new, *args, **kwargs):
        handle_result_enums(req.context['result'])

    @staticmethod
    def after_get(req, resp, collection, *args, **kwargs):
        handle_result_enums(req.context['result'])

    @staticmethod
    def after_patch(req, resp, *args, **kwargs):
        handle_result_enums(req.context['result'])


class GameResource(SingleResource):
    model = Game

    @staticmethod
    def after_get(req, resp, collection, *args, **kwargs):
        handle_result_enums(req.context['result'])

    @staticmethod
    def after_patch(req, resp, *args, **kwargs):
        handle_result_enums(req.context['result'])

    @staticmethod
    def after_delete(req, resp, item, *args, **kwargs):
        resp.status = falcon.HTTP_NO_CONTENT
        req.context['result'] = None


##########
# falcon_autocrud + json.dump doesn't handle Enum types correctly,
#   this function patches around that issue. [patch submitted]
######
def handle_result_enums(result):
    collected = result['data']
    if isinstance(collected, list):
        for each in collected:
            if 'state' in each:
                each['state'] = each['state'].name
    else:
        if 'state' in collected:
            collected['state'] = collected['state'].name
