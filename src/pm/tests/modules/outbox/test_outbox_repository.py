from pm.modules.outbox.repository import OutboxRepository
from pm.tests.modules.outbox.mixins import OutboxTestMixin


class TestOutboxRepository(OutboxTestMixin):
    def test_send_messages_error_after_some_sent(self, db_session):
        """If an error occurs while sending messages, we need to make sure
        we save all successfully sent messages."""
        message_count = 50
        num_to_send = 25
        self.generate_messages(db_session, message_count)
        with db_session() as session:
            try:
                for message in OutboxRepository(session).get_unsent():
                    if message.id > num_to_send:
                        # if we get to a message with an id > num_to_send, raise an
                        # error to simulate an error occurring while sending messages
                        raise Exception()
            except Exception:
                pass

            messages = self.get_all_messages(db_session)
            assert len(messages) == message_count
            for message in messages:
                # assert that all messages with an id <= num_to_send have been sent
                # the rest should not have been sent
                assert message.is_sent == (message.id <= num_to_send)
