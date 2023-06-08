from confluent_kafka import Message

from shared.tasks.consumer import SingleMessageConsumer


class MockSingleMessageConsumer(SingleMessageConsumer):
    def listen(self):
        """The same as the listen method on the consumer, but errors will not be caught.
        This lets us catch them in the test
        """
        msg: Message
        for msg in self.consumer:
            topic = msg.topic()
            if self.topics_consumers_lookup.get(topic):
                self.execute_consumers_on_topic(message=msg)
            else:
                raise NotImplementedError(f"No handler function for {topic}")
