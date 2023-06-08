from unittest.mock import Mock
from uuid import uuid4

import pytest
from confluent_kafka import Message
from factory import fuzzy
from marshmallow import ValidationError

from pm.consumers.der_warehouse import handlers
from pm.consumers.event.handle_service_provider_der_association_message import (
    handle_service_provider_der_message,
)
from pm.data_transfer_objects.csv_upload_kafka_messages import (
    EnrollmentRequestMessage,
    ServiceProviderDERAssociateMessage,
)
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.enums import EnrollmentCRUDStatus
from pm.modules.enrollment.repository import EnrollmentRequestRepository
from pm.tests import factories
from pm.tests.consumer.mocks import MockSingleMessageConsumer
from shared.minio_manager import convert_strings_to_float


class TestDerWHHandlers:
    def test_handle_der(self, der_payload_bytes, db_session):
        consumer = [
            Mock(
                spec=Message,
                topic=lambda: handlers.DER_WAREHOUSE_DER_TOPIC,
                value=lambda: der_payload_bytes,
                headers=lambda: [("service_provider_id", b"1")],
            ),
        ]
        topic_handlers = {handlers.DER_WAREHOUSE_DER_TOPIC: [handlers.handle_derwh_der]}
        MockSingleMessageConsumer(consumer=consumer, topics=topic_handlers).listen()


class TestEnrollDerIntoServiceProvider:
    def _get_all_ders(self, db_session) -> list[DerInfo]:
        with db_session() as session:
            return session.query(DerInfo).all()

    def test_enroll_der_into_service_provider(self, db_session):
        sp = factories.ServiceProviderFactory()
        der_id = uuid4()
        factories.DerFactory(der_id=der_id)
        test_message = ServiceProviderDERAssociateMessage(
            der_id=str(der_id),
        )
        test_message.set_headers({"service_provider_id": sp.id})
        handle_service_provider_der_message([test_message])
        ders = self._get_all_ders(db_session)
        assert len(ders) == 1


class TestEnrollmentRequest:
    def test_enrollment_process_message(self, db_session):
        factories.ProgramFactory(id=101)
        factories.ServiceProviderFactory(id=40)
        factories.DerFactory(
            der_id=1001,
            service_provider_id=40,
        )
        e_obj = EnrollmentRequestMessage(
            der_id="1001",
            import_active_limit="50",
            export_active_limit="50",
            import_reactive_limit="50",
            export_reactive_limit="50",
            import_target_capacity="30",
            export_target_capacity="30",
        )
        e_obj.headers["program_id"] = 101
        r = e_obj.process_message()
        with db_session() as session:
            saved_enrollment_obj = EnrollmentRequestRepository(
                session
            ).get_enrollment_request_or_raise(enrollment_request_id=1)
            assert r["id"] == saved_enrollment_obj.id
            assert r["status"] == EnrollmentCRUDStatus.CREATED

    def test_enrollment_missing_fields(self):
        data = {
            "DER_ID": "_de079cb9-f3ec-4a96-8305-df773eea8b99",
            "Default Limits - Active Power Import (kW) (optional)": "50",
            "Default Limits - Active Power Export (kW) (optional)": "50",
            "Default Limits - Reactive Power Import (kW) (optional)": "50",
            "Default Limits - Reactive Power Export (kW) (optional)": "50",
            "Import Target capacity (kW) (optional)": "22",
            "Export Target Capacity (kW) (optional)": "",
        }

        e = EnrollmentRequestMessage.schema().load(data)
        assert e.export_target_capacity == ""

    def test_convert_string_to_float(self):
        assert convert_strings_to_float("") is None
        assert convert_strings_to_float(" ") is None
        assert convert_strings_to_float("    ") is None
        assert convert_strings_to_float("1") == 1.0
        assert convert_strings_to_float("-10") == -10.0
        assert convert_strings_to_float(" 12   ") == 12.0
        val1 = fuzzy.FuzzyFloat(-10).fuzz()
        assert convert_strings_to_float(str(val1)) == val1
        str_val = fuzzy.FuzzyText().fuzz()
        with pytest.raises(ValidationError):
            convert_strings_to_float(str_val)
            convert_strings_to_float("    test_string ")
