from copy import deepcopy
from unittest.mock import Mock

from der_gateway_relay.consumer import DER_GATEWAY_PROGRAM_TOPIC
from der_gateway_relay.domain.payloads import (
    CreatePayload,
    DeletePayload,
    Operation,
    Payload,
    UpdatePayload,
)
from shared.enums import ProgramTypeEnum
from shared.tasks.consumer import ConsumerMessage


def make_consumer(value, operation=Operation.CREATED.name, count=100):
    headers = {"operation": operation}
    return [
        Mock(
            spec=ConsumerMessage,
            topic=DER_GATEWAY_PROGRAM_TOPIC,
            headers=headers,
            value=value,
        )
        for _ in range(count)
    ]


class TestPayload:
    def test_get_original_data(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload, count=3)
        payloads, _ = Payload.validate_and_sort(records)
        expected = [
            der_gateway_program_payload,
            der_gateway_program_payload,
            der_gateway_program_payload,
        ]

        got = payloads[0].raw_data
        assert got == expected

    def test_validate_and_sort_same_records(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload)
        payloads, failures = Payload.validate_and_sort(records)
        assert len(payloads) == 1
        assert payloads[0].operation == Operation.CREATED
        assert len(payloads[0].data) == 100
        assert len(failures) == 0

    def test_validate_and_sort_different_records(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload, count=30)
        records += make_consumer(
            der_gateway_program_payload, operation=Operation.UPDATED.name, count=1
        )
        records += make_consumer(der_gateway_program_payload, count=29)
        records += make_consumer(
            der_gateway_program_payload, operation=Operation.DELETED.name, count=1
        )
        records += make_consumer(der_gateway_program_payload, count=39)
        payloads, failures = Payload.validate_and_sort(records)
        assert len(payloads) == 5
        assert len(failures) == 0

        assert payloads[0].operation == Operation.CREATED
        assert isinstance(payloads[0], CreatePayload)
        assert len(payloads[0].data) == 30

        assert payloads[1].operation == Operation.UPDATED
        assert isinstance(payloads[1], UpdatePayload)
        assert len(payloads[1].data) == 1

        assert payloads[2].operation == Operation.CREATED
        assert isinstance(payloads[2], CreatePayload)
        assert len(payloads[2].data) == 29

        assert payloads[3].operation == Operation.DELETED
        assert isinstance(payloads[3], DeletePayload)
        assert len(payloads[3].data) == 1

        assert payloads[4].operation == Operation.CREATED
        assert isinstance(payloads[4], CreatePayload)
        assert len(payloads[4].data) == 39

    def test_validate_and_sort_20_invalid_records(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload, count=20)
        # these will fail validation
        records += make_consumer({}, count=20)
        records += make_consumer(der_gateway_program_payload, count=20)

        payloads, failures = Payload.validate_and_sort(records)
        assert len(payloads) == 1
        assert payloads[0].operation == Operation.CREATED
        assert len(payloads[0].data) == 40
        assert len(failures) == 20

    def test_validate_and_sort_bad_header(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload, count=50)
        records += make_consumer(der_gateway_program_payload, operation="invalidvalue", count=50)
        payloads, failures = Payload.validate_and_sort(records)
        assert len(payloads) == 1
        assert payloads[0].operation == Operation.CREATED
        assert len(payloads[0].data) == 50
        assert len(failures) == 50

    def test_der_program_data_validates_fields(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload, count=1)
        valid_payload_generic_program = deepcopy(der_gateway_program_payload)
        valid_payload_generic_program["program"]["program_type"] = ProgramTypeEnum.GENERIC.value
        valid_doe_program = deepcopy(der_gateway_program_payload)
        valid_doe_program["program"][
            "program_type"
        ] = ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES.value
        records += make_consumer(valid_payload_generic_program, count=1)
        records += make_consumer(valid_doe_program, count=1)
        payloads, failures = Payload.validate_and_sort(records)
        assert len(payloads) == 1
        assert payloads[0].operation == Operation.CREATED
        assert len(payloads[0].data) == 3
        assert len(failures) == 0

    def test_der_program_data_validates_fields_fails(self, der_gateway_program_payload):
        records = make_consumer(der_gateway_program_payload, count=1)  # will pass
        valid_payload_generic_program = deepcopy(der_gateway_program_payload)
        valid_payload_generic_program["program"]["program_type"] = ProgramTypeEnum.GENERIC.value
        valid_payload_generic_program["program"]["control_options"] = None
        valid_doe_program = deepcopy(der_gateway_program_payload)
        valid_doe_program["program"][
            "program_type"
        ] = ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES.value
        valid_doe_program["program"]["control_type"] = None
        records += make_consumer(valid_payload_generic_program, count=1)  # will fail
        records += make_consumer(valid_doe_program, count=1)  # will fail
        payloads, failures = Payload.validate_and_sort(records)
        assert len(payloads) == 1
        assert payloads[0].operation == Operation.CREATED
        assert len(payloads[0].data) == 1
        assert len(failures) == 2
