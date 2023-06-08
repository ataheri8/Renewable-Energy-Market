from unittest.mock import Mock

import pytest
from confluent_kafka import Message

from pm.consumers.contract import handlers
from pm.modules.enrollment.contract_repository import ContractRepository
from pm.tests import factories
from pm.tests.consumer.mocks import MockSingleMessageConsumer
from pm.topics import ContractMessage
from shared.tasks.producer import Producer


class TestContractHandler:
    def test_handle_contract_no_enrollment(self, contract_payload, db_session):
        class MockRepo(ContractRepository):
            def get_enrollment_and_program_by_contract_id(self, contract_id):
                return None

        data = ContractMessage.from_dict(contract_payload)

        with pytest.raises(ValueError):
            handlers.handle_contract(data, headers={"operation": "create"}, Repository=MockRepo)
        # Kafka producer not called if it is None
        assert Producer._producer is None

    def test_handle_contract(self, contract_payload_bytes, db_session):
        program = factories.GenericProgramFactory(id=1)
        service_provider = factories.ServiceProviderFactory(id=1)
        enrollment = factories.EnrollmentRequestFactory(
            id=1, program=program, service_provider=service_provider
        )
        factories.ContractFactory(
            id=1, enrollment_request=enrollment, program=program, service_provider=service_provider
        )
        consumer = [
            Mock(
                spec=Message,
                topic=lambda: ContractMessage.TOPIC,
                value=lambda: contract_payload_bytes,
                headers=lambda: [("operation", b"create")],
            ),
        ]
        topic_handlers = {ContractMessage.TOPIC: [handlers.handle_contract]}
        MockSingleMessageConsumer(consumer=consumer, topics=topic_handlers).listen()
        # assert Kafka producer was called
        assert Producer._producer.produce.call_count == 1
