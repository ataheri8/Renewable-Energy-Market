from __future__ import annotations

import abc
import json
from collections import defaultdict
from typing import Optional, Tuple

from confluent_kafka import Consumer as KafkaConsumer
from confluent_kafka import Message
from confluent_kafka.admin import AdminClient, NewTopic

from shared.minio_manager import Message as KafkaCustomMessage
from shared.system import loggingsys
from shared.tasks.decorators import (
    ConsumerType,
    RegisterTopic,
    registered_topic_handlers,
)

# Timing constants
ONE_SECOND = 1.0
KAFKA_POLL_INTERVAL = ONE_SECOND


logger = loggingsys.get_logger(name=__name__)

# TODO allow some Kafka topics to be processed in parallel
# TODO allow retries on error with backoff


def create_kafka_topics(kafka_url: str):
    """Create Kafka topics if they don't exist."""
    admin_client = AdminClient({"bootstrap.servers": kafka_url})
    logger.info("Creating topics...")
    topic_list = [NewTopic(t, num_partitions=1) for t in registered_topic_handlers.keys()]
    fs = admin_client.create_topics(topic_list)

    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            logger.info(f"Topic {topic} created")
        except Exception as e:
            logger.info(f"Failed to create topic {topic}: {e}")


class Consumer(abc.ABC):
    def __init__(self, consumer: KafkaConsumer, topics: RegisterTopic):
        self.consumer = consumer
        self.topics_consumers_lookup = topics

    def _subscribe(self):
        """Subscribe to topics."""
        self.consumer.subscribe(list(self.topics_consumers_lookup.keys()))
        logger.info(
            f"Listening for the following topics: {self._get_topic_list_and_function_count()}"
        )

    def _get_topic_list_and_function_count(self):
        # console message: topics are being listened to
        # & how many functions are listening to each topic
        return " ; ".join(
            [
                f"{k} has {len(self.topics_consumers_lookup[k])} consumer"
                for k in self.topics_consumers_lookup.keys()
            ]
        )

    @staticmethod
    def filter_topics(
        topic_handlers: RegisterTopic,
        include_topics: Optional[list[str]],
        consumer_type: ConsumerType,
    ) -> RegisterTopic:
        """Filter topics based on include list. If no list is provided, return all topics."""
        topics: RegisterTopic = {}
        topic_names = topic_handlers.keys()
        if include_topics:
            for topic in include_topics:
                if topic not in topic_names:
                    raise ValueError(
                        f"Included topic '{topic}' not found in registered topics. "
                        + "Did you register the handler with the decorator "
                        + "and import the module containing the handler? \n"
                        + f"Registered topics: {list(topic_names)} \n"
                        + "See the consumer's docstring for instructions on registering topics."
                    )
        for topic, handlers in topic_handlers.items():
            handlers_filtered = [fn for fn in handlers if fn.consumer_type == consumer_type]
            if include_topics and topic not in include_topics:
                continue
            if handlers_filtered:
                topics[topic] = handlers_filtered
        if not topics:
            raise ValueError(f"No available topic handlers for consumer type {consumer_type.value}")
        return topics

    @staticmethod
    def make_kafka_consumer(url: str, group_id: str) -> KafkaConsumer:
        """Creates a KafkaConsumer object.
        See https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md for options
        """
        conf = {
            "bootstrap.servers": url,
            "group.id": group_id,
            "session.timeout.ms": 6000,
            "on_commit": lambda err, partitions: print("Committed offsets: ", partitions),
            "auto.offset.reset": "earliest",
        }
        return KafkaConsumer(conf)

    @classmethod
    @abc.abstractmethod
    def factory(
        cls,
        include_topics: Optional[list[str]],
        url: str = "localhost:9092",
        group_id: str = "mygroup",
        **kwargs,
    ) -> Consumer:
        pass

    @abc.abstractmethod
    def listen(self):
        """Start the consumer. Listens for incoming messages and sends them
        to the right handler(s)."""


class SingleMessageConsumer(Consumer):
    """Consumes one message at a time and passes it on to a handler,
    using the registered topic handlers.

    example usage:
        @register_topic_handler("some-topic", MyMarshmallowSchema())
        def handle_some_topic(data: dict, headers: dict | None = None):
            ...

    The module containing the handler must be imported in the file where the consumer is created.

    example:
        from pm.consumers.event import handlers as event_handlers

    This is ideal for low frequency messages, and is the default strategy.
    """

    def convert_header_to_dict(self, headers: list[Tuple]):
        """example: [('TOPIC', b'service_provider'), ('service_provider_id', b'9998'),
        ('FILE_TYPE', b'SERVICE_PROVIDER'),
        ('row_number', b'1'), ('approx_row_count', b'22')]

        Note headers values are all strings.
        """
        headers = headers or []
        return {k: v.decode("utf-8") for k, v in headers}

    def execute_consumers_on_topic(self, message: Message):
        # Message is a 'confluent_kafka.Message' not one of our 'Message' dataclass
        try:
            consumer_functions = self.topics_consumers_lookup[message.topic()]
            for fn in consumer_functions:
                try:
                    # can't type hint them or the line is too long & mypy has a problem
                    messages: list
                    if fn.schema:
                        messages = fn.schema.loads(message.value())
                    else:
                        # convert from bytestring to json
                        messages = json.loads(message.value().decode("utf-8"))
                    header_dict: dict = self.convert_header_to_dict(message.headers())
                    self.set_each_message_with_shared_header(header_dict, messages)
                    fn(
                        data=messages,
                        headers=header_dict,
                    )
                except Exception as e:
                    logger.error(f"Error executing consumer: {fn.__name__} : {e}", exc_info=True)
        except KeyError as e:
            logger.info(f"Message on topic '{message.topic}' has no consumer : {e}")

    def set_each_message_with_shared_header(self, header_dict, list_of_messages):
        try:
            self.get_messages_class(list_of_messages).batch_set_header(
                list_of_messages, header_dict
            )
        except Exception as e:
            logger.info(f"Error setting header on messages: {e}")

    def get_messages_class(
        self, list_of_messages: list[KafkaCustomMessage]
    ) -> type[KafkaCustomMessage]:
        # given a list of messages, return the class of the first message
        return list_of_messages[0].__class__

    def listen(self):
        self._subscribe()
        try:
            while True:
                msg: Message = self.consumer.poll(KAFKA_POLL_INTERVAL)
                if msg is None:
                    continue
                if msg.error():
                    logger.error("Consumer error: {}".format(msg.error()))
                    continue
                self.execute_consumers_on_topic(message=msg)
        finally:
            self.consumer.close()

    @classmethod
    def factory(
        cls,
        include_topics: Optional[list[str]],
        url: str = "localhost:9092",
        group_id: str = "mygroup",
        **kwargs,
    ) -> SingleMessageConsumer:
        """Creates the Kafka consumer and filters topics based on the include list.

        If no topics are specified, all available topics will be consumed."""
        topics = cls.filter_topics(
            topic_handlers=registered_topic_handlers,
            include_topics=include_topics,
            consumer_type=ConsumerType.SINGLE,
        )
        consumer = cls.make_kafka_consumer(url=url, group_id=group_id)
        return SingleMessageConsumer(consumer=consumer, topics=topics)


class ConsumerMessage:
    """Wrapper for Kafka message with headers and deserialized value."""

    headers: dict[str, str]
    value: dict

    def __init__(self, kafka_message: Message):
        if kafka_message.headers() is not None:
            self.headers = {k: v.decode("utf-8") for k, v in kafka_message.headers()}
        message = kafka_message.value()
        self.value = json.loads(message.decode("utf-8"))

    @classmethod
    def from_message_list_sort_by_topic(
        cls, kafka_message_list: list[Message]
    ) -> dict[str, list[ConsumerMessage]]:
        messages: dict[str, list[ConsumerMessage]] = defaultdict(list)
        for msg in kafka_message_list:
            if not msg.error() and msg.value():
                messages[msg.topic()].append(cls(msg))
        return messages


class BatchMessageConsumer(Consumer):
    """Consumes messages in batches and passes lists of messages to the handler.

    example usage:
        @register_topic_handler("some-topic", consumer_type=ConsumerType.BATCH)
        def handle_some_topic(data: list[ConsumerMessage]):
            ...

    The module containing the handler must be imported in the file where the consumer is created.

    example:
        from pm.consumers.event import handlers as event_handlers

    Suited for topics that have frequent messages. The messages will not be validated
    against a schema, and will be passed as a list of ConsumerMessage objects.
    """

    def __init__(
        self,
        consumer: KafkaConsumer,
        topics: RegisterTopic,
        max_bulk_messages: int = 500,
        bulk_timeout_seconds: int = 1,
    ):
        self.max_bulk_messages = max_bulk_messages
        self.bulk_timeout_seconds = bulk_timeout_seconds
        super().__init__(consumer, topics)

    def send_messages_to_handler(self, messages: list[Message]):
        consumer_messages = ConsumerMessage.from_message_list_sort_by_topic(messages)
        for topic, message_list in consumer_messages.items():
            try:
                consumer_functions = self.topics_consumers_lookup[topic]
                for fn in consumer_functions:
                    try:
                        fn(data=message_list)
                    except Exception as e:
                        logger.error(
                            f"Error executing consumer: {fn.__name__} : {e}", exc_info=True
                        )
            except KeyError as e:
                logger.info(f"Message on topic '{topic}' has no consumer : {e}")

    def listen(self):
        """Listen for messages and pass them to the handler(s)."""
        self._subscribe()
        try:
            while True:
                messages = self.consumer.consume(
                    self.max_bulk_messages, timeout=self.bulk_timeout_seconds
                )
                logger.info(f"Consumed {len(messages)} messages")
                if messages:
                    self.send_messages_to_handler(messages=messages)
        finally:
            self.consumer.close()

    @classmethod
    def factory(
        cls,
        include_topics: Optional[list[str]] = None,
        url: str = "localhost:9092",
        group_id: str = "mygroup",
        **kwargs,
    ) -> BatchMessageConsumer:
        """Creates the Kafka consumer and filters topics based on the include list.

        If no topics are specified, all available topics will be consumed.

        Accepts the following additional keyword arguments for the Kafka consumer:
            max_bulk_messages - int: max number of messages to consume in one batch (default 500)
            bulk_timeout_seconds - int: max time to wait for messages in one batch (default 1)
        """
        max_bulk_messages = kwargs.get("max_bulk_messages", 500)
        bulk_timeout_seconds = kwargs.get("bulk_timeout_seconds", 1)
        topics = cls.filter_topics(
            topic_handlers=registered_topic_handlers,
            include_topics=include_topics,
            consumer_type=ConsumerType.BATCH,
        )
        consumer = cls.make_kafka_consumer(url=url, group_id=group_id)
        return BatchMessageConsumer(
            consumer=consumer,
            topics=topics,
            max_bulk_messages=max_bulk_messages,
            bulk_timeout_seconds=bulk_timeout_seconds,
        )
