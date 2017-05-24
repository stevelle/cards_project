import json

import falcon

from falcon_autocrud.resource import CollectionResource, SingleResource

from card_table import commands
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
    ##########
    # falcon_autocrud + json.dump doesn't handle Enum types correctly,
    #   this function patches around that issue. [patch submitted]
    ######
    @staticmethod
    def _serialize_all_enums(clasz, target):
        """ Helper to serialize Enums for each item in target

        :param clasz: a class which implements serialize_enums(item)
        :param target: where to search for items
        """
        data = target['data']
        if isinstance(data, list):
            for item in data:
                clasz.serialize_enums(item)
        else:
            clasz.serialize_enums(data)

    ##########
    # transform particular subdicts to strings when inbound, to store as Text
    ######
    @staticmethod
    def _serialize_all_dicts(clasz, target):
        """ Helper to serialize Dicts for each item in target

        :param clasz: a class which implements serialize_dicts(item)
        :param target: where to search for items
        """
        data = target['data']
        if isinstance(data, list):
            for item in data:
                clasz.serialize_dicts(item)
        else:
            clasz.serialize_dicts(data)


class Protected(object):

    IMMUTABLE_PROPERTY = 'This property is not modifiable.'

    def before_patch(self, req, resp, db_session, resource, *args, **kwargs):
        """ Common handling of protected / immutable properties """
        frozen_props = self._protected_props() + self._immutable_props()
        for forbidden in frozen_props:
            if forbidden in req.context['doc']:
                raise falcon.HTTPInvalidParam(msg=self.IMMUTABLE_PROPERTY,
                                              param_name=forbidden)

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        """ Common handling of protected properties """
        for forbidden in self._protected_props():
            if forbidden in req.context['doc']:
                raise falcon.HTTPInvalidParam(msg=self.IMMUTABLE_PROPERTY,
                                              param_name=forbidden)

    def _protected_props(self):
        """ Enumerates read-only properties """
        return [p.name for p in self.model.protected_properties()]

    def _immutable_props(self):
        return [p.name for p in self.model.immutable_properties()]


class RestResource(SingleResource, Protected, ResourceHelper):

    @staticmethod
    def after_delete(req, resp, item, *args, **kwargs):
        """ Common handler fixes up behavior of DELETE requests """
        resp.status = falcon.HTTP_NO_CONTENT
        req.context['result'] = None


class CommandCollectionResource(CollectionResource, Protected, ResourceHelper):
    model = Command

    def before_post(self, req, resp, db_session, resource, *args, **kwargs):
        super(CommandCollectionResource, self).before_post(
            req, resp, db_session, resource, *args, **kwargs)
        commands.execute(db_session, resource)

    def after_get(self, req, resp, new, *args, **kwargs):
        self._serialize_all_dicts(CommandResource, req.context['result'])

    def after_post(self, req, resp, new, *args, **kwargs):
        self._serialize_all_dicts(CommandResource, req.context['result'])


class CommandResource(RestResource):
    model = Command

    def modify_patch(self, req, resp, resource, *args, **kwargs):
        if getattr(resource, 'changes', None):
            resource.changes = json.dumps(resource.changes)

    def after_get(self, req, resp, collection, *args, **kwargs):
        self._serialize_all_dicts(self.__class__, req.context['result'])

    def after_patch(self, req, resp, *args, **kwargs):
        self._serialize_all_dicts(self.__class__, req.context['result'])

    @staticmethod
    def serialize_dicts(item):
        if 'changes' in item:
            changes = item['changes'].replace("'", '"')
            item['changes'] = json.loads(changes)


class CardCollectionResource(CollectionResource, Protected, ResourceHelper):
    model = Card
    # TODO validate the card is landing in a valid stack, in the same game

    def after_post(self, req, resp, new, *args, **kwargs):
        self._serialize_all_enums(CardResource, req.context['result'])

    def after_get(self, req, resp, collection, *args, **kwargs):
        self._serialize_all_enums(CardResource, req.context['result'])

    def after_patch(self, req, resp, *args, **kwargs):
        self._serialize_all_enums(CardResource, req.context['result'])


class CardResource(RestResource):
    model = Card
    # TODO validate the card is landing in a valid stack, in the same game

    def after_get(self, req, resp, collection, *args, **kwargs):
        self._serialize_all_enums(self.__class__, req.context['result'])

    def after_patch(self, req, resp, *args, **kwargs):
        self._serialize_all_enums(self.__class__, req.context['result'])

    @staticmethod
    def serialize_enums(thing):
        if 'owner_facing' in thing:
            thing['owner_facing'] = thing['owner_facing'].name
        if 'other_facing' in thing:
            thing['other_facing'] = thing['other_facing'].name


class StackCollectionResource(CollectionResource):
    model = Stack
    # TODO validate the stack is in a valid game


class StackResource(RestResource):
    model = Stack
    # TODO validate the stack is in a valid game


class GameCollectionResource(CollectionResource, Protected, ResourceHelper):
    model = Game

    def after_post(self, req, resp, new, *args, **kwargs):
        self._serialize_all_enums(GameResource, req.context['result'])

    def after_get(self, req, resp, collection, *args, **kwargs):
        self._serialize_all_enums(GameResource, req.context['result'])

    def after_patch(self, req, resp, *args, **kwargs):
        self._serialize_all_enums(GameResource, req.context['result'])


class GameResource(RestResource):
    model = Game

    def after_get(self, req, resp, collection, *args, **kwargs):
        self._serialize_all_enums(self.__class__, req.context['result'])

    def after_patch(self, req, resp, *args, **kwargs):
        self._serialize_all_enums(self.__class__, req.context['result'])

    @staticmethod
    def serialize_enums(thing):
        if 'state' in thing:
            thing['state'] = thing['state'].name
