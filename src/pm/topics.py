from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

from dataclasses_json import DataClassJsonMixin, config
from marshmallow import fields
from sqlalchemy.orm import Session

from pm.modules.enrollment.enums import (
    ContractStatus,
    ContractType,
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.enrollment.models.enrollment import (
    DemandResponseDict,
    DynamicOperatingEnvelopesDict,
)
from pm.modules.outbox.model import Outbox
from shared.tasks.producer import MessageData, SendToKafkaMessage
from shared.utils import convert_datetimes_and_enums_to_string
from shared.validators.der_gateway_data import DerGatewayProgram


@dataclass
class OutboxMessage(MessageData):
    """Adds a message to the outbox table."""

    @classmethod
    def add_to_outbox(cls, session: Session, body: dict, headers: Optional[dict] = None):
        """Adds an Outbox record to the session.
        The message will then be sent to Kafka by the scheduler.
        """
        message = cls(**body)
        message.headers = headers or {}
        outbox = Outbox(
            topic=message.TOPIC,
            headers=convert_datetimes_and_enums_to_string(message.headers),
            message=convert_datetimes_and_enums_to_string(asdict(message)),
        )
        session.add(outbox)


@dataclass
class EnrollmentMessage(OutboxMessage, DataClassJsonMixin):
    TOPIC = "pm.enrollment"

    id: int
    created_at: datetime
    updated_at: datetime
    program_id: int
    service_provider_id: int
    der_id: str
    enrollment_status: EnrollmentRequestStatus
    dynamic_operating_envelopes: Optional[DynamicOperatingEnvelopesDict] = None
    demand_response: Optional[DemandResponseDict] = None
    rejection_reason: Optional[EnrollmentRejectionReason] = None


@dataclass
class ContractMessage(OutboxMessage, DataClassJsonMixin):
    TOPIC = "pm.contract"
    headers = {"operation": ""}

    id: int
    created_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    updated_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    enrollment_request_id: int
    program_id: int
    service_provider_id: int
    der_id: str
    contract_status: ContractStatus
    contract_type: ContractType
    dynamic_operating_envelopes: Optional[DynamicOperatingEnvelopesDict] = None
    demand_response: Optional[DemandResponseDict] = None


@dataclass
class DerGatewayProgramMessage(SendToKafkaMessage, DerGatewayProgram, DataClassJsonMixin):
    TOPIC = "der-gateway-program"
    headers = {"operation": "create"}


DOCUMENTED_TOPICS = [EnrollmentMessage, ContractMessage, DerGatewayProgramMessage]
