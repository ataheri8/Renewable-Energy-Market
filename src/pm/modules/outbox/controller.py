from pm.modules.outbox.repository import OutboxRepository
from shared.repository import UOW
from shared.tasks.producer import Producer


class OutboxUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.repository = OutboxRepository(self.session)
        return self


class OutboxController:
    def __init__(self):
        self.unit_of_work = OutboxUOW()

    def send_message(self):
        """Send a message to the message broker."""
        with self.unit_of_work as uow:
            for message in uow.repository.get_unsent():
                Producer.send_json(
                    topic=message.topic,
                    json_str=message.get_json(),
                    headers=message.headers,
                )
                # flush each time, effectively making this a synchronous call
                # this is required because we want to commit the transaction
                # after each message is sent
                Producer.flush()
