from __future__ import annotations

import json

from sqlalchemy import Boolean, Column, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import JSONB

from shared.model import CreatedAtUpdatedAtMixin
from shared.system.database import Base


class Outbox(CreatedAtUpdatedAtMixin, Base):
    """Transactional outbox table for sending messages to the message broker.

    Instead of sending messages directly to the message broker, we store
    them in the database and send them from a background task.

    This is required because we want to be able to send Kafka messages from within a transaction,
    which is important for ensuring data consistency. If we send the message directly to kafka,
    we can't guarantee that the message will be sent and the transaction will be committed.
    """

    __tablename__ = "outbox"
    id: int = Column(Integer, primary_key=True)
    topic: str = Column(UnicodeText, nullable=False)
    headers: dict = Column(JSONB, nullable=True)
    message: dict = Column(JSONB, nullable=False)
    is_sent: bool = Column(Boolean, nullable=False, default=False, index=True)

    def get_json(self) -> str:
        """Get the message as a json string."""
        return json.dumps(self.message)
