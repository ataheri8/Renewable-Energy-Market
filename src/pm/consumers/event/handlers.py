from pm.data_transfer_objects.csv_upload_kafka_messages import ServiceProviderMessage
from shared.minio_manager import FakeMessage, Message
from shared.system.loggingsys import get_logger
from shared.tasks.decorators import register_topic_handler

logger = get_logger(__name__)


@register_topic_handler(
    FakeMessage.Meta.topic,
    schema=FakeMessage.schema(many=True),
)  # type: ignore
def handle_fake_message(data: list[Message], headers: dict | None = None):
    FakeMessage.process_messages(list_of_messages=data)


@register_topic_handler("pm.service_provider_enrollment", ServiceProviderMessage.schema(many=True))
def handle_service_provider_enrollment(
    data: list[Message], headers: dict = None  # type: ignore #noqa
):  # type: ignore #noqa
    logger.info("handle service provider enrollment")
    ServiceProviderMessage.process_messages(data)
