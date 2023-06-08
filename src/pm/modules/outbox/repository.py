from typing import Generator

from sqlalchemy import select

from pm.modules.outbox.model import Outbox
from shared.repository import SQLRepository
from shared.system import loggingsys

logger = loggingsys.get_logger(name=__name__)


class OutboxRepository(SQLRepository):
    def get_unsent(self) -> Generator[Outbox, None, None]:
        """Get all unsent messages from the outbox."""
        stmt = select(Outbox).where(Outbox.is_sent.is_(False)).order_by(Outbox.id)
        records = self.session.execute(stmt).scalars().all()
        for r in records:
            yield r
            r.is_sent = True
            self.session.add(r)
            # we want to commit every successful sent message, since the
            # message broker might get blocked if kafka is down
            self.session.commit()
        logger.info(f"Sent {len(records)} messages from the outbox.")
