from __future__ import annotations

import abc
import enum
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

from marshmallow import ValidationError

from der_gateway_relay.builders.program import BuildEnrollmentXML, BuildProgramXML
from der_gateway_relay.builders.provision_program import ProvisionProgramBuilder
from der_gateway_relay.services.api_service import ApiService
from der_gateway_relay.topics import DerGatewayFailure
from shared.system import loggingsys
from shared.tasks.consumer import ConsumerMessage
from shared.validators.der_gateway_data import DerGatewayProgram

logger = loggingsys.get_logger(__name__)


class Operation(enum.Enum):
    CREATED = enum.auto()
    UPDATED = enum.auto()
    DELETED = enum.auto()


@dataclass
class Payload(abc.ABC):
    """Base class for payloads.

    Payloads are used to group messages by operation and then generate the XML for the operation.
    There are three types of payloads: create, update, and delete.
    The factory method will generate the correct concrete class based on the operation.
    """

    operation: Operation
    data: list[DerGatewayProgram] = field(default_factory=list)
    raw_data: list[dict] = field(default_factory=list)  # kept for error reporting

    def __post_init__(self):
        self.enrollment_builder = BuildEnrollmentXML
        self.program_builder = BuildProgramXML
        self.provision_builder = ProvisionProgramBuilder

    def has_data(self) -> bool:
        return bool(self.data)

    def add(self, program: DerGatewayProgram, raw_data: dict[str, Any]):
        """Add a program to the payload"""
        self.data.append(program)
        self.raw_data.append(raw_data)

    @abc.abstractmethod
    def send_payload(self, api_service: ApiService):
        pass

    @classmethod
    def factory(cls, op: Operation) -> Payload:
        """Generate the correct payload class based on the operation"""
        if op == Operation.CREATED:
            return CreatePayload(op)
        elif op == Operation.UPDATED:
            return UpdatePayload(op)
        elif op == Operation.DELETED:
            return DeletePayload(op)
        else:
            raise NotImplementedError(f"Operation {op} is not implemented")

    @classmethod
    def validate_and_sort(
        cls, data: list[ConsumerMessage]
    ) -> Tuple[list[Payload], list[DerGatewayFailure]]:
        """Validate the data from the der gateway program topic and sort it into groups.
        Groups are defined by the operation type. If the operation type changes, the group
        is closed and a new group is started.

        If they fail validation, add them to the failed list
        """
        payload: Optional[Payload] = None
        payloads: list[Payload] = []
        failed: list[DerGatewayFailure] = []
        schema = DerGatewayProgram.schema()
        for record in data:
            try:
                # check headers for operation are valid
                op = Operation[record.headers["operation"]]
                valid_data: DerGatewayProgram = schema.load(record.value)
                if not payload:
                    payload = cls.factory(op)
                elif op != payload.operation:
                    payloads.append(payload)
                    payload = cls.factory(op)
                payload.add(valid_data, record.value)
            except (ValidationError, KeyError) as e:
                msg = f"DER Gateway Relay error: {e} \n cannot process data"
                logger.error(msg, exc_info=True)
                failure = DerGatewayFailure(
                    message=msg,
                    sent_headers=record.headers,
                    data=record.value,
                    reason="validation-failed",
                )
                failed.append(failure)
        # catch the last payload if it has data
        if payload and payload.has_data():
            payloads.append(payload)
        return payloads, failed


class CreatePayload(Payload):
    """Payload for create operations. Will generate the XML for the create operation"""

    def send_payload(self, api_service: ApiService):
        # create the new program and enrollment
        create_program_xml = self.program_builder.build(self.data, action="add")
        api_service.post_program(create_program_xml)

        create_enrollment_xml = self.enrollment_builder.build(self.data, action="add")
        api_service.post_enrollment(create_enrollment_xml)

        provision_program = self.provision_builder.build(create_program_xml)
        api_service.post_provision_program(provision_program)


class UpdatePayload(Payload):
    """Payload for update operations. Will generate the XML for the update operation"""

    def send_payload(self, api_service: ApiService):
        # update the existing program and enrollment
        update_program_xml = self.program_builder.build(self.data, action="update")
        api_service.post_program(update_program_xml)

        update_enrollment_xml = self.enrollment_builder.build(self.data, action="update")
        api_service.post_enrollment(update_enrollment_xml)


class DeletePayload(Payload):
    """Payload for delete operations. Will generate the XML for the delete operation"""

    def send_payload(self, api_service: ApiService):
        # delete the existing program and enrollment
        delete_program_xml = self.program_builder.build(self.data, action="remove")
        api_service.post_program(delete_program_xml)

        delete_enrollment_xml = self.enrollment_builder.build(self.data, action="remove")
        api_service.post_enrollment(delete_enrollment_xml)
