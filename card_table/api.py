import json

import falcon

from falcon_autocrud.resource import CollectionResource, SingleResource

from card_table.storage import db_verifier, Game, Stack, Card


def create_api(middleware, db_engine):
    app = falcon.API(middleware=middleware)
    app.add_route('/health', HealthResource(db_engine))
    app.add_route('/games', GameCollectionResource(db_engine))
    app.add_route('/games/{id}', GameResource(db_engine))
    app.add_route('/stacks', StackCollectionResource(db_engine))
    app.add_route('/stacks/{id}', StackResource(db_engine))
    app.add_route('/cards', CardCollectionResource(db_engine))
    app.add_route('/cards/{id}', CardResource(db_engine))
    return app


class HealthResource(object):

    error_txt = 'Service failed health check'
    ok_txt = json.dumps({'title': '200 OK',
                         'description': 'Service passed health check'})

    def __init__(self, db_engine):
        self.is_db_available = db_verifier(db_engine)

    def on_get(self, req, resp):
        # PoC: always OK
        if self.is_db_available():
            resp.status = falcon.HTTP_200
            resp.body = self.ok_txt
        else:
            raise falcon.HTTPServiceUnavailable(description=self.error_txt,
                                                retry_after=60)


class RestResource(SingleResource):
    """ Convenience class that fixes up behavior of DELETE requests """
    @staticmethod
    def after_delete(req, resp, item, *args, **kwargs):
        resp.status = falcon.HTTP_NO_CONTENT
        req.context['result'] = None


class GameCollectionResource(CollectionResource):
    model = Game

    @staticmethod
    def after_post(req, resp, new, *args, **kwargs):
        _serialize_all_enums(req.context['result'])

    @staticmethod
    def after_get(req, resp, collection, *args, **kwargs):
        _serialize_all_enums(req.context['result'])

    @staticmethod
    def after_patch(req, resp, *args, **kwargs):
        _serialize_all_enums(req.context['result'])


class GameResource(RestResource):
    model = Game

    @staticmethod
    def after_get(req, resp, collection, *args, **kwargs):
        _serialize_all_enums(req.context['result'])

    @staticmethod
    def after_patch(req, resp, *args, **kwargs):
        _serialize_all_enums(req.context['result'])


class StackCollectionResource(CollectionResource):
    model = Stack


class StackResource(RestResource):
    model = Stack


class CardCollectionResource(CollectionResource):
    model = Card

    @staticmethod
    def after_post(req, resp, new, *args, **kwargs):
        _serialize_all_enums(req.context['result'])

    @staticmethod
    def after_get(req, resp, collection, *args, **kwargs):
        _serialize_all_enums(req.context['result'])

    @staticmethod
    def after_patch(req, resp, *args, **kwargs):
        _serialize_all_enums(req.context['result'])


class CardResource(RestResource):
    model = Card

    @staticmethod
    def after_get(req, resp, collection, *args, **kwargs):
        _serialize_all_enums(req.context['result'])

    @staticmethod
    def after_patch(req, resp, *args, **kwargs):
        _serialize_all_enums(req.context['result'])


##########
# falcon_autocrud + json.dump doesn't handle Enum types correctly,
#   this function patches around that issue. [patch submitted]
######
def _serialize_all_enums(result):
    data = result['data']
    if isinstance(data, list):
        for item in data:
            __serialize_enums_for_model(item)
    else:
        __serialize_enums_for_model(data)


def __serialize_enums_for_model(thing):
    # Games
    if 'state' in thing:
        thing['state'] = thing['state'].name
    # Cards
    if 'owner_facing' in thing:
        thing['owner_facing'] = thing['owner_facing'].name
    if 'other_facing' in thing:
        thing['other_facing'] = thing['other_facing'].name
