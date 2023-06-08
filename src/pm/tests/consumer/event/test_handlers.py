from unittest import mock

import pytest
from marshmallow import ValidationError

from pm.consumers.event.handle_enrollment_create_message import (
    handle_enrollment_create_control,
    handle_enrollment_request_message,
)
from pm.consumers.event.handlers import (
    handle_fake_message,
    handle_service_provider_enrollment,
)
from pm.data_transfer_objects.csv_upload_kafka_messages import (
    EnrollmentRequestMessage,
    ServiceProviderMessage,
)
from pm.modules.enrollment.controller import EnrollmentController
from pm.modules.enrollment.repository import EnrollmentRequestRepository
from pm.modules.enrollment.services.enrollment import EnrollmentRequestGenericFieldsDict
from pm.modules.serviceprovider import models
from pm.tests.factories import DynamicOperatingEnvelopesProgram
from shared.minio_manager import FakeMessage, Message


class TestServiceProviderMessage:
    def test_service_provider_message_invalid_status(self, db_session):
        with pytest.raises(ValidationError):
            ServiceProviderMessage(
                name="Service Provider Name",
                service_provider_type="AGGREGATOR",
                primary_contact="Contact Name",
                primary_email="contact@domain.com",
                notification_contact="Contact Name",
                notification_email="contact@domain.com",
                street_address="123 Address St",
                apt_unit="Unit 001",
                city="Edmonton",
                state_province_region="Alberta",
                country="Canada",
                zip_postal_code="H3H 8E8",
                status="BAD DATA",
            )

    def test_service_provider_message_invalid_type(self, db_session):
        with pytest.raises(ValidationError):
            ServiceProviderMessage(
                name="Service Provider Name",
                service_provider_type="BAD TYPE",
                primary_contact="Contact Name",
                primary_email="contact@domain.com",
                notification_contact="Contact Name",
                notification_email="contact@domain.com",
                street_address="123 Address St",
                apt_unit="Unit 001",
                city="Edmonton",
                state_province_region="Alberta",
                country="Canada",
                zip_postal_code="H3H 8E8",
                status="ACTIVE",
            )

    def test_service_provider_message_schema(self, db_session):
        """Here we want to test the alternate field names the CSV can have."""
        data_dict = {
            "Name": "Service Provider Name",  # name
            "Type": "AGGREGATOR",  # service_provider_type
            "Primary contact": "Contact Name Primary",  # primary_contact
            "Primary email": "contact@domain.com",  # primary_email
            "Notification contact": "Contact Name Notify",  # notification_contact
            "Notification email": "contact@domain.com",  # notification_email
            "Street Address": "123 Address St",  # street_address
            "Apt/unit": "Unit 001",  # apt_unit
            "City": "Edmonton",  # city
            "State/Province/Region": "Alberta",  # state_province_region
            "Country": "Canada",  # country
            "ZIP/Postal Code": "H3H 8E8",  # zip_postal_code
            "Status": "ACTIVE",  # status
        }

        spam = ServiceProviderMessage.schema().load(data_dict)
        assert spam.name == "Service Provider Name"
        assert spam.service_provider_type == "AGGREGATOR"
        assert spam.primary_contact == "Contact Name Primary"
        assert spam.primary_email == "contact@domain.com"
        assert spam.notification_contact == "Contact Name Notify"
        assert spam.notification_email == "contact@domain.com"
        assert spam.street_address == "123 Address St"
        assert spam.apt_unit == "Unit 001"
        assert spam.city == "Edmonton"
        assert spam.state_province_region == "Alberta"
        assert spam.country == "Canada"
        assert spam.zip_postal_code == "H3H 8E8"
        assert spam.apt_unit == "Unit 001"
        assert spam.status == "ACTIVE"

    def test_service_provider_message_to_db_valid(self, db_session):
        spam = ServiceProviderMessage(
            name="Service Provider Name",
            service_provider_type="AGGREGATOR",
            primary_contact="Contact Name",
            primary_email="contact@domain.com",
            notification_contact="Contact Name",
            notification_email="contact@domain.com",
            street_address="123 Address St",
            apt_unit="Unit 001",
            city="Edmonton",
            state_province_region="Alberta",
            country="Canada",
            zip_postal_code="H3H 8E8",
            status="ACTIVE",
        )
        spam.process_message()
        service_providers = None
        with db_session() as session:
            service_providers = session.query(models.ServiceProvider).all()
        assert len(service_providers) == 1

    def test_service_provider_message_to_db_blank_notifications(self, db_session):
        spam = ServiceProviderMessage(
            name="Service Provider Name",
            service_provider_type="AGGREGATOR",
            primary_contact="Contact Name",
            primary_email="contact@domain.com",
            notification_contact=None,
            notification_email="contact@domain.com",
            street_address="123 Address St",
            apt_unit="Unit 001",
            city="Edmonton",
            state_province_region="Alberta",
            country="Canada",
            zip_postal_code="H3H 8E8",
            status="ACTIVE",
        )
        spam.process_message()
        service_providers = None
        with db_session() as session:
            service_providers = session.query(models.ServiceProvider).all()
        assert len(service_providers) == 1
        result = service_providers[0]
        assert result.name == "Service Provider Name"
        assert result.notification_contact is None

    def test_upsert_behaviour(
        self,
        db_session,
        fake_enrollment_data,
    ):
        # https://opusonesolutions.atlassian.net/browse/PM-686
        # new data should update previously supplied records
        with db_session() as session:
            all_enrollment_requests = EnrollmentController().get_all_enrollment_requests()
            assert len(all_enrollment_requests) == 0
            program_id = 3
            DynamicOperatingEnvelopesProgram(
                id=program_id,
                name="DOE",
            )
            e1 = EnrollmentRequestMessage(
                der_id=fake_enrollment_data["der_id"],
                import_active_limit="13",
                import_reactive_limit="17",
                export_active_limit="19",
                export_reactive_limit="21",
                import_target_capacity="23",
                export_target_capacity="27",
            )
            e1.set_headers({"program_id": program_id})
            e1.process_message()
            currently_enrollment_requests = EnrollmentController().get_all_enrollment_requests()
            assert len(currently_enrollment_requests) == 1
            assert (
                currently_enrollment_requests[0].dynamic_operating_envelopes[
                    "default_limits_active_power_export_kw"
                ]
                == 19
            )
            e2 = EnrollmentRequestMessage(
                der_id=fake_enrollment_data["der_id"],
                import_active_limit="131",
                import_reactive_limit="117",
                export_active_limit="234",
                export_reactive_limit="211",
                import_target_capacity="231",
                export_target_capacity="271",
            )
            e2.set_headers({"program_id": program_id})
            e2.process_message()

        currently_enrollment_requests = EnrollmentRequestRepository(
            session
        ).get_enrollments_for_report(program_id)
        assert len(currently_enrollment_requests) == 1
        assert (
            currently_enrollment_requests[0].dynamic_operating_envelopes[
                "default_limits_active_power_export_kw"
            ]
            == 234
        )

    def test_handle_fake_message(self):
        fake_message_mock = mock.Mock(spec=FakeMessage)
        with mock.patch("pm.consumers.event.handlers.FakeMessage", fake_message_mock):
            messages = [mock.Mock(spec=Message)]
            expected_count = len(messages)
            handle_fake_message(messages)
            assert fake_message_mock.process_messages.call_count == 1
            args = fake_message_mock.process_messages.call_args[1]["list_of_messages"]
            assert isinstance(args, list)
            assert len(args) == expected_count

    def test_handle_service_provider_enrollment(self):
        sp_message_mock = mock.Mock(spec=ServiceProviderMessage)
        with mock.patch("pm.consumers.event.handlers.ServiceProviderMessage", sp_message_mock):
            messages = [mock.Mock(spec=Message)]
            expected_count = len(messages)
            handle_service_provider_enrollment(messages)
            assert sp_message_mock.process_messages.call_count == 1
            args = sp_message_mock.process_messages.call_args[0][0]
            assert isinstance(args, list)
            assert len(args) == expected_count

    def test_handle_enrollment_request_message(self):
        enrollment_message_mock = mock.Mock(spec=ServiceProviderMessage)
        with mock.patch(
            "pm.consumers.event.handle_enrollment_create_message.EnrollmentRequestMessage",
            enrollment_message_mock,
        ):
            messages = [mock.Mock(spec=Message)]
            expected_count = len(messages)
            handle_enrollment_request_message(messages)
            assert enrollment_message_mock.process_messages.call_count == 1
            args = enrollment_message_mock.process_messages.call_args[1]["list_of_messages"]
            assert isinstance(args, list)
            assert len(args) == expected_count

    def test_handle_enrollment_create_control(self):
        controller_mock = mock.Mock(spec=EnrollmentController)
        with mock.patch(
            "pm.consumers.event.handle_enrollment_create_message.EnrollmentController",
            controller_mock,
        ):
            messages = [
                mock.Mock(spec=EnrollmentRequestGenericFieldsDict),
                mock.Mock(spec=EnrollmentRequestGenericFieldsDict),
            ]
            expected_count = len(messages)
            handle_enrollment_create_control(messages)
            instance = controller_mock.return_value
            assert instance.create_enrollment_requests.call_count == expected_count
