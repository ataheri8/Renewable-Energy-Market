from datetime import datetime, timezone

import pytest

from pm.modules.enrollment.enums import EnrollmentRequestStatus
from pm.modules.enrollment.models.enrollment import EnrollmentRequest
from pm.modules.enrollment.repository import (
    EnrollmentNotFound,
    EnrollmentRequestRepository,
)
from pm.tests import factories


class TestEnrollmentRequestRepository:
    def _get_all_enrollment(self, db_session) -> list[EnrollmentRequest]:
        with db_session() as session:
            return session.query(EnrollmentRequest).all()

    def test_save_enrollment(self, db_session):
        with db_session() as session:
            enrollment_request_id = 1
            repo = EnrollmentRequestRepository(session)
            enrollment = repo.get(enrollment_request_id)
            assert enrollment is None
            # requires a program to exist
            factories.ProgramFactory(id=1)
            factories.ServiceProviderFactory(id=1)
            der = factories.DerFactory(service_provider_id=1)
            enrollment = EnrollmentRequest(
                program_id=1,
                service_provider_id=1,
                der_id=der.der_id,
                enrollment_status=EnrollmentRequestStatus.ACCEPTED,
                dynamic_operating_envelopes=dict(
                    default_limits_active_power_import_kw=50,
                    default_limits_active_power_export_kw=50,
                    default_limits_reactive_power_import_kw=50,
                    default_limits_reactive_power_export_kw=50,
                ),
                demand_response=dict(
                    import_target_capacity=300.01,
                    export_target_capacity=300.01,
                ),
            )
            repo.save_enrollment_request(enrollment)
            session.commit()
            enrollment = repo.get(enrollment_request_id)
            assert enrollment is not None

    def test_get_all(self, db_session):
        with db_session() as session:
            num_of_enrollments = 5
            for _ in range(num_of_enrollments):
                factories.EnrollmentRequestFactory()
            enrollments = EnrollmentRequestRepository(session).get_all()
            assert len(enrollments) == num_of_enrollments

    @pytest.mark.parametrize(
        "enrollment_exist",
        [
            pytest.param(True, id="one-enrollment"),
            pytest.param(False, id="zero-enrollment"),
        ],
    )
    def test_get(self, db_session, enrollment_exist):
        with db_session() as session:
            if enrollment_exist:
                factories.EnrollmentRequestFactory(id=1)
                enrollment = EnrollmentRequestRepository(session).get(1)
                assert enrollment is not None
                assert enrollment.id == 1
            else:
                enrollment = EnrollmentRequestRepository(session).get(1)
                assert enrollment is None

    @pytest.mark.parametrize(
        "enrollment_exist",
        [
            pytest.param(True, id="one-enrollment"),
            pytest.param(False, id="zero-enrollment"),
        ],
    )
    def test_get_enrollment_or_raise(self, db_session, enrollment_exist):
        with db_session() as session:
            if enrollment_exist:
                factories.EnrollmentRequestFactory(id=1)
                enrollment = EnrollmentRequestRepository(session).get_enrollment_request_or_raise(1)
                assert enrollment is not None
            else:
                with pytest.raises(EnrollmentNotFound):
                    EnrollmentRequestRepository(session).get_enrollment_request_or_raise(1)

    def test_get_enrollments_for_report(self, db_session):
        program_1 = factories.ProgramFactory(id=1)
        program_2 = factories.ProgramFactory(id=2)
        service_provider = factories.ServiceProviderFactory(id=1)
        der_1 = factories.DerFactory(der_id="der_1", service_provider_id=1)
        der_2 = factories.DerFactory(der_id="der_2", service_provider_id=1)
        der_3 = factories.DerFactory(der_id="der_3", service_provider_id=1)
        factories.EnrollmentRequestFactory(
            id=1,
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
        )
        enrollment_2 = factories.EnrollmentRequestFactory(
            id=2,
            program=program_1,
            service_provider=service_provider,
            der=der_2,
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            created_at=datetime(2022, 11, 8, tzinfo=timezone.utc),
        )
        enrollment_3 = factories.EnrollmentRequestFactory(
            id=3,
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            created_at=datetime(2022, 11, 9, tzinfo=timezone.utc),
        )
        factories.EnrollmentRequestFactory(
            id=4,
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.PENDING,
            created_at=datetime(2022, 11, 10, tzinfo=timezone.utc),
        )
        factories.EnrollmentRequestFactory(
            id=5,
            program=program_2,
            service_provider=service_provider,
            der=der_3,
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            created_at=datetime(2022, 11, 11, tzinfo=timezone.utc),
        )
        with db_session() as session:
            enrollments_1 = EnrollmentRequestRepository(session).get_enrollments_for_report(1)
        assert len(enrollments_1) == 2
        assert enrollments_1 == [enrollment_3, enrollment_2]
