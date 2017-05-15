import falcon


def create_api(middleware):
    app = falcon.API(middleware=middleware)
    app.add_route('/health', HealthResource())
    return app


class HealthResource(object):

    @staticmethod
    def on_get(req, resp):
        # PoC: always OK
        resp.status = falcon.HTTP_200
        resp.body = '{"status": "ok"}'
