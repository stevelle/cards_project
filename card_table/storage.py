import datetime as dt
import enum

import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import bindparam, select, Text
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum

Base = declarative_base()
LOG = logging.getLogger(__name__)


class Command(Base):
    """ Describes a step of play in a Game """
    __tablename__ = 'commands'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    actor_id = Column(Integer)
    operation = Column(String, index=True)
    """ json blob describing the changes made by the command """
    changes = Column(Text)
    memo = Column(String, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, index=True)

    @staticmethod
    def protected_properties():
        return [Command.id, Command.created_at, Command.updated_at]

    @staticmethod
    def immutable_properties():
        return [Command.game_id, Command.actor_id]


class Facing(enum.Enum):
    """ Describes visibility of a Card """
    down = 0b00
    """ Previously taken a peek """
    revealed = 0b01
    peeking = 0b10
    up = 0b11


class Card(Base):
    """ An individual card """
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    stack_id = Column(Integer, ForeignKey('stacks.id'))
    """ position == 0 indicates top or left """
    position = Column(Integer)
    owner_facing = Column(Enum(Facing), default=Facing.down)
    other_facing = Column(Enum(Facing), default=Facing.down)
    suit = Column(String, nullable=True)
    """ Effective sortable suit """
    suit_value = Column(String, nullable=True, default=suit)
    rank = Column(String, nullable=True)
    """ Effective sortable rank """
    rank_value = Column(Integer, nullable=True, default=rank)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, index=True)

    @staticmethod
    def get(record_id, db_session):
        return db_session.query(__class__).get(record_id)

    @staticmethod
    def find_by_stack(stack_id, db_session):
        return db_session.query(Card).filter(Card.stack_id == stack_id).all()

    @staticmethod
    def protected_properties():
        return [Card.id, Card.created_at, Card.updated_at]

    @staticmethod
    def immutable_properties():
        return []


class Stack(Base):
    """ A stack of cards """
    __tablename__ = 'stacks'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    """ owner_id == 0 : a shared stack, such as a shared draw pile """
    owner_id = Column(Integer, index=True)
    label = Column(String, index=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, index=True)
    # META-PROPERTIES, for use by a game engine to store state
    """ Indicates maximum visible size of the deck to observers.

    Cards at a depth > size_visibility will not be visible or countable by
    players who are not the owner of the stack.

    size_visibility IS NULL: all cards in the deck are visible and countable
    size_visibility == 0 : 0 cards in the deck are visible (a hidden stack)
    size_visibility == 1 : the deck shows size as either 0, or 1+ cards
    size_visibility == 2 : the deck shows size as 0, 1, or 2+ cards...
    """
    size_visibility = Column(Integer, nullable=True)
    """ An actual limit on the number of cards held in a stack. """
    size_limit = Column(Integer, nullable=True)

    @staticmethod
    def get(record_id, db_session):
        return db_session.query(__class__).get(record_id)

    @staticmethod
    def protected_properties():
        return [Stack.id, Stack.game_id, Stack.created_at, Stack.updated_at]

    @staticmethod
    def immutable_properties():
        return []


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

    @staticmethod
    def protected_properties():
        return [Game.id, Game.created_at, Game.updated_at]

    @staticmethod
    def immutable_properties():
        return []


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
