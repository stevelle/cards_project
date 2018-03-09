from falcon_autocrud.middleware import Middleware
from sqlalchemy import create_engine

from card_table import api, storage


def middleware():
    return [Middleware()]


def engine():
    db_engine = create_engine("sqlite:///:memory:")
    storage.sync(db_engine)
    return db_engine

application = api.create_api(middleware(), engine())
