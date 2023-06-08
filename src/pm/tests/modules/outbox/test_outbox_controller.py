from pm.modules.outbox.controller import OutboxController
from pm.tests.modules.outbox.mixins import OutboxTestMixin
from shared.tasks.producer import Producer


class TestOutboxController(OutboxTestMixin):
    def test_send_message(self, db_session):
        """If there are messages in the outbox, they should be sent."""
        message_count = 50
        self.generate_messages(db_session, message_count)
        OutboxController().send_message()
        assert Producer._producer.produce.call_count == message_count

        messages = self.get_all_messages(db_session)
        assert len(messages) == message_count
        assert all(message.is_sent for message in messages)

    def test_send_message_no_messages(self, db_session):
        """If there are no messages in the outbox, nothing should be sent,
        and no errors should be raised."""
        OutboxController().send_message()
        assert Producer._producer is None

        messages = self.get_all_messages(db_session)
        assert len(messages) == 0

    def test_send_messages_all_sent_messages(self, db_session):
        """Messages that have already been sent should not be sent again."""
        message_count = 50
        self.generate_messages(db_session, message_count, is_sent=True)
        OutboxController().send_message()
        assert Producer._producer is None

        messages = self.get_all_messages(db_session)
        assert len(messages) == message_count

    def test_send_messages_some_sent_messages(self, db_session):
        """Messages that have already been sent should not be sent again."""
        message_count = 50
        self.generate_messages(db_session, message_count, is_sent=True)
        self.generate_messages(db_session, message_count)
        OutboxController().send_message()
        assert Producer._producer.produce.call_count == message_count

        messages = self.get_all_messages(db_session)
        assert len(messages) == message_count * 2
        assert all(message.is_sent for message in messages)
