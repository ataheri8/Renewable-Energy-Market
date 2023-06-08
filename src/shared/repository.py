from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.selectable import Select

from shared.system.database import Session as S

T = TypeVar("T")


@dataclass
class PaginatedQuery(Generic[T]):
    pagination_start: int
    pagination_end: int
    count: int
    results: Sequence[T]


class UOW:
    def __enter__(self):
        self.session = S()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()


class SQLRepository:
    """Base repository class for a SQL repository.
    Implemented with SQLAlchemy
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def count(self, query: Select | Query) -> int:
        """Counts the rows returned by a query.
        Takes an optional session parameter which will be used if passed,
        otherwise a new session will be created
        """
        stmt = select(func.count()).select_from(query.subquery())
        return self.session.execute(stmt).scalar_one()

    def offset_paginate(self, query: Select | Query, start: int, end: int) -> PaginatedQuery:
        """Returns results in a PaginatedQuery object.
        WARNING don't use this to paginate large datasets!
        Takes an SQL Alchemy Query object and fetches all rows that match the query,
        limited by the `start` and `end` parameters.
        Also counts the total rows that match the query
        """
        results = (
            self.session.execute(query.offset(start - 1).limit(end - start + 1)).scalars().all()
        )
        # cancel ordering because it doesn't change the count
        query.order_by(None)
        count = self.count(query)
        return PaginatedQuery(
            pagination_start=start,
            pagination_end=end,
            results=results,
            count=count,
        )

    def save(self, entity) -> int:
        """Save an entity"""
        id = None
        self.session.add(entity)
        self.session.flush()
        # ID is now in object since transaction has been flushed
        id = entity.id
        return id

    def save_all(self, entities: list):
        """Save a list of entities"""
        self.session.add_all(entities)
