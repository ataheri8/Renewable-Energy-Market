from pm.modules.outbox.model import Outbox


class OutboxTestMixin:
    def generate_messages(self, db_session, num_messages: int, is_sent=False) -> None:
        """Generate a number of messages in the outbox."""
        with db_session() as session:
            for _ in range(num_messages):
                session.add(
                    Outbox(
                        topic="test",
                        message={"test": "test"},
                        headers={"test": "test"},
                        is_sent=is_sent,
                    )
                )
            session.commit()

    def get_all_messages(self, db_session) -> list[Outbox]:
        """Get all messages from the outbox."""
        with db_session() as session:
            return session.query(Outbox).all()
