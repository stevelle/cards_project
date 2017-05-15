import falcon

from falcon_autocrud.resource import CollectionResource, SingleResource

from card_table.storage import Game


def create_api(middleware, db_engine):
    app = falcon.API(middleware=middleware)
    app.add_route('/health', HealthResource())
    app.add_route('/games', GameCollectionResource(db_engine))
    app.add_route('/games/{id}', GameResource(db_engine))
    return app


class HealthResource(object):

    @staticmethod
    def on_get(req, resp):
        # PoC: always OK
        resp.status = falcon.HTTP_200
        resp.body = '{"status": "ok"}'


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
