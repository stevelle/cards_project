import datetime as dt
import enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer, String, Enum

Base = declarative_base()


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
