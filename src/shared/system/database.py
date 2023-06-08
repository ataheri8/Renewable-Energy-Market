"""Handle database connection logic"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    RelationshipProperty,
    class_mapper,
    scoped_session,
    sessionmaker,
)
from sqlalchemy.orm.collections import InstrumentedList

from shared.system.configuration import Config

ENGINE: Engine | None = None


class SQLAlchemyBase:
    def to_dict(self, include_relationships=True) -> dict:
        """Create a dictionary from this model.
        Optionally include loaded relationships (but not nested relationships).
        """
        props = {}
        for c in class_mapper(self.__class__).columns:
            props[c.key] = getattr(self, c.key)
            # check if c.key is a dataclass
            if hasattr(props[c.key], "to_dict"):
                props[c.key] = props[c.key].to_dict()

        if include_relationships:
            for prop in class_mapper(self.__class__).iterate_properties:
                if isinstance(prop, RelationshipProperty) and prop.key in self.__dict__:
                    related_obj = getattr(self, prop.key)
                    if related_obj is not None:
                        if isinstance(related_obj, InstrumentedList):
                            props[prop.key] = [
                                obj.to_dict(include_relationships=False) for obj in related_obj
                            ]
                        elif not isinstance(related_obj, RelationshipProperty):
                            props[prop.key] = related_obj.to_dict(include_relationships=False)
        return props


Base = declarative_base(cls=SQLAlchemyBase)

Session = scoped_session(sessionmaker())


def get_pgdsn(user: str, password: str, host: str, port: int, dbname: str) -> str:
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def pgdsn_from_config(config: Config) -> str:
    return get_pgdsn(
        config.DB_USERNAME,
        config.DB_PASSWORD,
        config.DB_HOST,
        config.DB_PORT,
        config.DB_NAME,
    )


def make_engine(pgdsn: str) -> Engine:
    return create_engine(pgdsn, future=True)


def get_engine() -> Engine:
    if ENGINE is None:
        raise Exception(
            "SQLAlchemy DB Engine has not been created yet. "
            "This is normally done in database.init()"
        )
    return ENGINE


def init(config: Config, session_expire_on_commit=True):
    global ENGINE
    from . import loggingsys

    loggingsys.get_logger(__name__)
    pgdsn = pgdsn_from_config(config)
    engine = make_engine(pgdsn)
    if not ENGINE:
        ENGINE = engine
        Session.configure(bind=engine, expire_on_commit=session_expire_on_commit)
