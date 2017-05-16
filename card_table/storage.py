import datetime as dt
import enum

import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import bindparam, select
from sqlalchemy import Column, DateTime, Integer, String, Enum

Base = declarative_base()
LOG = logging.getLogger(__name__)


class GameState(enum.Enum):
    forming = 0
    starting = 1
    cancelled = 2
    playing = 3
    paused = 4
    abandoned = 5
    finished = 6


class Game(Base):
    """ An individual game at a specific table """
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    state = Column(Enum(GameState), default=GameState.forming)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, index=True)


def sync(engine):
    Base.metadata.create_all(engine)


def db_verifier(db_engine):

    _statement = select([Game.__table__]).where(Game.id == bindparam('id'))
    _compiled_cache = {}

    def is_available():
        func = db_engine.connect
        cache = _compiled_cache
        try:
            with (func().execution_options(compiled_cache=cache)) as conn:
                conn.execute(_statement, id=1).first()
            return True

        except Exception as e:
            LOG.error('Failure at DB during health check {}'.format(str(e)))
            return False

    return is_available
