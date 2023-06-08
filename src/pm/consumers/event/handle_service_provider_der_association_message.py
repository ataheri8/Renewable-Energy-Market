from pm.data_transfer_objects.csv_upload_kafka_messages import (
    ServiceProviderDERAssociateMessage,
)
from shared.minio_manager import Message
from shared.tasks.decorators import register_topic_handler


@register_topic_handler(
    ServiceProviderDERAssociateMessage.Meta.topic,
    schema=ServiceProviderDERAssociateMessage.schema(many=True),
)
def handle_service_provider_der_message(data: list[Message], headers: dict | None = None):
    ServiceProviderDERAssociateMessage.process_messages(list_of_messages=data)
