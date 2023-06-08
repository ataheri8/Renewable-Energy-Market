from __future__ import annotations

from typing import Optional

from der_gateway_relay.config import DerGatewayRelayConfig
from der_gateway_relay.domain.payloads import Payload
from der_gateway_relay.services.api_service import ApiService
from der_gateway_relay.topics import DerGatewayFailure
from shared.system.loggingsys import get_logger
from shared.tasks.consumer import ConsumerMessage
from shared.tasks.decorators import ConsumerType, register_topic_handler

logger = get_logger(__name__)


@register_topic_handler(
    DerGatewayRelayConfig.DER_GATEWAY_PROGRAM_TOPIC, consumer_type=ConsumerType.BATCH
)
def handle_der_gateway_program(
    data: list[ConsumerMessage], api_service: Optional[ApiService] = None
):
    """Handle the data from the der gateway program topic."""
    logger.info(f"Received {len(data)} records from der-gateway-program topic")
    payloads, failed = Payload.validate_and_sort(data)
    # generate the payloads from the validated data and send them to DER Gateway
    if api_service is None:
        api_service = ApiService()
    for payload in payloads:
        try:
            payload.send_payload(api_service)
        except Exception as e:
            msg = f"Error sending payload to DER Gateway: {e}"
            logger.error(msg, exc_info=True)
            failed += [
                DerGatewayFailure(
                    message=msg,
                    sent_headers={"operation": payload.operation.value},
                    data=data,
                    reason="der-gateway-error",
                )
                for data in payload.raw_data
            ]
    # log the failed validation messages and send them to Kafka der-gateway-failure topic
    for failure in failed:
        failure.send_to_kafka()
