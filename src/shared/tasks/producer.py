import abc
import enum
import json
from dataclasses import asdict, dataclass
from typing import Any, List, Tuple

from confluent_kafka import Producer as KafkaProducer
from confluent_kafka.error import ProduceError

from shared.system import configuration
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


@dataclass
class MessageData(abc.ABC):
    """Base class for topic data.

    Child classes must include the TOPIC name.

    Child classes should also be dataclass, and optional extra information for
    documenting fields can be added using the fields metadata keyword argument.

    ex.
    @dataclass
    MyTopic(TopicData):
        TOPIC = 'shared.example-topic'

        example_field: str
        example_field_with_docs: str = field(
            metadata={
                "description": "This is an example field",
                "example": "example field content example"
            }
        )
    """

    # don't add type hints here, it will break the api spec generation
    # & inheritance
    TOPIC = ""  # type: ignore
    headers = {}  # type: ignore


@dataclass
class SendToKafkaMessage(MessageData):
    """Adds the send_to_kafka method, which sends the message to Kafka directly."""

    def send_to_kafka(self):
        Producer.send_message(message=self, topic=self.TOPIC, headers=self.headers)


def handle_enum(obj: Any) -> Any:
    if isinstance(obj, enum.Enum):
        return obj.value
    return str(obj)


class Producer:
    _producer: KafkaProducer = None

    @classmethod
    def generate_header(cls, headers: dict) -> List[Tuple]:
        """headers is a list of tuples
        of string + bytes
        generate_header({"a": "1", "b": "2"})
        >>> [("a", b"1"), ("b", b"2")]
        """
        return [(k, handle_enum(v).encode("utf-8")) for k, v in headers.items()]

    @classmethod
    def send_message(
        cls,
        topic: str,
        message,
        headers: dict | None = None,
    ):
        """Sends a message on a Kafka topic.
        The topic should be a json_dataclass type
        """
        topic_data = json.dumps(asdict(message), default=handle_enum)
        cls.send_json(topic=topic, json_str=topic_data, headers=headers)

    @classmethod
    def send_json(
        cls,
        topic: str,
        json_str: str,
        headers: dict | None = None,
    ):
        """Sends a message on a Kafka topic.
                The topic should be a json_dataclass type
        json_str should be a json string
        '{"a": 1, "b": "a"}'
        """
        config = configuration.get_config()
        headers = headers or {}
        headers_byte_list: List[Tuple] = cls.generate_header(headers)
        cls._producer = cls._producer or KafkaProducer({"bootstrap.servers": config.KAFKA_URL})
        # serialize to bytes here so we can catch errors in our tests
        topic_data = json_str.encode("utf-8")
        try:
            cls._producer.produce(
                topic=topic,
                value=topic_data,
                headers=headers_byte_list,
                callback=lambda err, msg: logger.info(f"Kafka message sent: {msg}"),
            )
        except ProduceError as error:
            logger.error(f"Kafka error: {error}")
            raise error

    @classmethod
    def flush(cls):
        config = configuration.get_config()
        cls._producer = cls._producer or KafkaProducer({"bootstrap.servers": config.KAFKA_URL})
        cls._producer.flush()
