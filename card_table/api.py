import json

import falcon

from falcon_autocrud.resource import CollectionResource, SingleResource

from card_table import commands
from card_table.common import ensure_modifiable, require_record
from card_table.storage import db_verifier, Game, Stack, Card, Command


def create_api(middleware, db_engine):
    app = falcon.API(middleware=middleware)
    app.add_route('/health', HealthResource(db_engine))
    app.add_route('/games', GameCollectionResource(db_engine))
    app.add_route('/games/{id}', GameResource(db_engine))
    app.add_route('/stacks', StackCollectionResource(db_engine))
    app.add_route('/stacks/{id}', StackResource(db_engine))
    app.add_route('/cards', CardCollectionResource(db_engine))
    app.add_route('/cards/{id}', CardResource(db_engine))
    app.add_route('/commands', CommandCollectionResource(db_engine))
    app.add_route('/commands/{id}', CommandResource(db_engine))
    return app


class HealthResource(object):

    error_txt = 'Service failed health check'
    ok_txt = json.dumps({'title': '200 OK',
                         'description': 'Service passed health check'})

    def __init__(self, db_engine):
        self.is_db_available = db_verifier(db_engine)

    def on_get(self, req, resp):
        if self.is_db_available():
            resp.status = falcon.HTTP_200
            resp.body = self.ok_txt
        else:
            raise falcon.HTTPServiceUnavailable(description=self.error_txt,
                                                retry_after=60)


class ResourceHelper(object):
    """ Helper for Resources to serialize Enum and Dict in responses """

    def after_get(self, req, resp, collection, *args, **kwargs):
        self._serialize_all_enums(self.model, req.context['result'])

    def after_patch(self, req, resp, *args, **kwargs):
        self._serialize_all_enums(self.model, req.context['result'])

    def after_post(self, req, resp, new, *args, **kwargs):
        self._serialize_all_enums(self.model, req.context['result'])

    # falcon_autocrud + json.dump doesn't handle Enum types correctly,
    #   this function patches around that issue. [patch submitted]
    # transform particular subdicts to strings when inbound, to store as Text
    @staticmethod
    def _serialize_all_enums(model, target):
        """ Helper to serialize special field types for each item in target

        :param model: a class which implements serialize_specials(item)
        :param target: where to search for items
        """
        data = target['data']
        try:
            if isinstance(data, list):
                for item in data:
                    model.serialize_specials(item)
            else:
                model.serialize_specials(data)
        except AttributeError:
            # may not be implemented
            pass


class Protected(object):

    IMMUTABLE_PROPERTY = 'This property is not modifiable.'

    def before_patch(self, req, resp, db_session, resource, *args, **kwargs):
        """ Common handling of protected / immutable properties """
        ensure_modifiable(self.model, req.context['doc'])

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        """ Common handling of protected properties """
        ensure_modifiable(self.model, req.context['doc'],
                          allow_immutables=True)


class RestCollectionResource(CollectionResource, Protected, ResourceHelper):
    pass


class RestResource(SingleResource, Protected, ResourceHelper):

    @staticmethod
    def after_delete(req, resp, item, *args, **kwargs):
        """ Common handler fixes up behavior of DELETE requests """
        resp.status = falcon.HTTP_NO_CONTENT
        req.context['result'] = None


class CommandCollectionResource(RestCollectionResource):
    model = Command

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        super(CommandCollectionResource, self).before_post(
            req, resp, db_session, resource, *args, **kwargs)

        commands.execute(db_session, resource)


class CommandResource(RestResource):
    model = Command

    def modify_patch(self, req, resp, resource, *args, **kwargs):
        super(CommandResource, self).modify_patch(
            req, resp, resource, *args, **kwargs)

        if getattr(resource, 'changes', None):
            resource.changes = json.dumps(resource.changes)


class CardCollectionResource(RestCollectionResource):
    model = Card

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        super(CardCollectionResource, self).before_post(
            req, resp, db_session, resource, *args, **kwargs)

        require_record(db_session, Stack, 'stack_id', req.context['doc'])


class CardResource(RestResource):
    model = Card
    # TODO validate the card is landing in a valid stack, in the same game?


class StackCollectionResource(RestCollectionResource):
    model = Stack

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        super(StackCollectionResource, self).before_post(
            req, resp, db_session, resource, *args, **kwargs)

        require_record(db_session, Game, 'game_id', req.context['doc'])


class StackResource(RestResource):
    model = Stack
    # TODO validate the stack is in a valid game?


class GameCollectionResource(RestCollectionResource):
    model = Game


class GameResource(RestResource):
    model = Game
