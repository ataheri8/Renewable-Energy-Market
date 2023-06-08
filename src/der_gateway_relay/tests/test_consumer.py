from unittest.mock import Mock

from der_gateway_relay.config import DerGatewayRelayConfig
from der_gateway_relay.consumer import handle_der_gateway_program
from der_gateway_relay.domain import payloads
from der_gateway_relay.services.api_service import ApiService
from shared.tasks.consumer import ConsumerMessage
from shared.tasks.producer import Producer

DER_GATEWAY_PROGRAM_TOPIC = DerGatewayRelayConfig.DER_GATEWAY_PROGRAM_TOPIC


def make_consumer(value, operation=payloads.Operation.CREATED.name, count=100):
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


def test_consumer(der_gateway_program_payload):
    data = make_consumer(der_gateway_program_payload, count=100)
    api_service = Mock(spec=ApiService)
    handle_der_gateway_program(data, api_service)
    # check no messages were sent to Kafka
    assert Producer._producer is None
    # check the api service was called the correct number of times
    assert api_service.post_program.call_count == 1
    assert api_service.post_enrollment.call_count == 1
    assert api_service.post_provision_program.call_count == 1


def test_consumer_multiple_payloads(der_gateway_program_payload):
    data = make_consumer(der_gateway_program_payload, count=30)
    data += make_consumer(
        der_gateway_program_payload, operation=payloads.Operation.UPDATED.name, count=1
    )
    data += make_consumer(der_gateway_program_payload, count=29)
    api_service = Mock(spec=ApiService)
    handle_der_gateway_program(data, api_service)
    # check no messages were sent to Kafka
    assert Producer._producer is None
    # check the api service was called the correct number of times
    # called 4 times because update calls create and delete
    assert api_service.post_program.call_count == 3
    assert api_service.post_enrollment.call_count == 3
    # provision program is only called on create, which make up 2 of the payloads
    assert api_service.post_provision_program.call_count == 2


def test_consumer_with_failures(der_gateway_program_payload):
    valid_count = 30
    invalid_count = 30
    data = make_consumer(der_gateway_program_payload, count=valid_count)
    data += make_consumer({}, count=invalid_count)  # should fail and send to dead letter queue
    api_service = Mock(spec=ApiService)
    handle_der_gateway_program(data, api_service)
    # check failed records were sent to Kafka
    assert Producer._producer.produce.call_count == invalid_count
    # check the api service was called the correct number of times
    assert api_service.post_program.call_count == 1
    assert api_service.post_enrollment.call_count == 1
    assert api_service.post_provision_program.call_count == 1


def test_ConsumerMessage_from_message_list():
    kafka_message = Mock()
    attrs = {
        "value.return_value": b'{"der_gateway_program": {"program_id": "1234"}}',
        "headers.return_value": [("operation", b"CREATED")],
        "error.return_value": None,
    }
    kafka_message.configure_mock(**attrs)
    assert kafka_message.headers()
    data = ConsumerMessage(kafka_message=kafka_message)
    assert data.value == {"der_gateway_program": {"program_id": "1234"}}
    assert data.headers == {"operation": "CREATED"}
    msg_list = ConsumerMessage.from_message_list_sort_by_topic([kafka_message])
    assert len(msg_list.values()) == 1
