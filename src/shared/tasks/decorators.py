import logging
from collections import defaultdict
from enum import Enum
from typing import Optional, Protocol

from marshmallow import Schema

logger = logging.getLogger(__name__)


class ConsumerType(Enum):
    SINGLE = "SINGLE"
    BATCH = "BATCH"


class RegisterTopicHandlerDecorator(Protocol):
    """Protocol for the register_topic_handler decorator.
    This is used to type hint the decorator.
    """

    schema: Optional[Schema]
    consumer_type: ConsumerType

    def __name__(self) -> str:
        ...

    def __call__(self, *args, **kwargs) -> None:
        ...


# alias for the type hint because it's long!
RegisterTopic = dict[str, list[RegisterTopicHandlerDecorator]]

registered_topic_handlers: RegisterTopic = defaultdict(list)


def register_topic_handler(
    event: str,
    schema: Optional[Schema] = None,
    consumer_type: ConsumerType = ConsumerType.SINGLE,
):
    """Registers a handler for a kafka topic.
    Takes in an event (topic) and a marshmallow schema to validate
    the payload.

    Single consumers (the default) can take an optional marshmallow schema
    to validate the payload. If the schema is not provided, the payload will
    not be validated.

    Batch consumers will not validate the payload, and will pass a list of
    ConsumerMessages to the handler.

    example usage:
        @register_topic_handler("some-topic", MyMarshmallowSchema())
        def handle_some_topic(data: dict, headers: dict | None = None):
            ...
    """

    def decorator(func):
        if consumer_type == ConsumerType.BATCH and schema:
            raise ValueError(
                "Batch consumers do not support schema validation. "
                "Please remove the schema argument."
            )
        func.consumer_type = consumer_type
        func.schema = schema
        registered_topic_handlers[event].append(func)
        return func

    return decorator
