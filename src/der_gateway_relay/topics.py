from dataclasses import dataclass, field

from shared.tasks.producer import SendToKafkaMessage


@dataclass
class DerGatewayFailure(SendToKafkaMessage):
    """Topic for DER Gateway failure events"""

    TOPIC = "der_gateway_failure"

    message: str
    reason: str
    sent_headers: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
