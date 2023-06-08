from http import HTTPStatus

import pytest

from pm.modules.serviceprovider.enums import ServiceProviderStatus
from pm.tests import factories
from shared.enums import ProgramTypeEnum


class TestEnrollment:
    def test_get_all_enrollments(self, client, db_session):
        factories.EnrollmentRequestFactory()
        resp = client.get("/api/enrollment/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 1
        factories.EnrollmentRequestFactory()
        resp = client.get("/api/enrollment/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 2

    def test_get_enrollment_success(self, client, db_session):
        enrollment = factories.EnrollmentRequestFactory(id=1)
        resp = client.get("/api/enrollment/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["der_id"] == enrollment.der_id

    def test_get_enrollment_fail(self, client, db_session):
        factories.EnrollmentRequestFactory(id=1)
        resp = client.get("/api/enrollment/2")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(
        "body,program_type,response",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
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
                ),
                ProgramTypeEnum.DEMAND_MANAGEMENT,
                "NOT_CREATED",
                id="all-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    )
                ),
                ProgramTypeEnum.GENERIC,
                "NOT_CREATED",
                id="minimum-fields",
            ),
        ],
    )
    def test_create_enrollment_single_der_failed_inactive_service_provider(
        self, client, db_session, body, program_type, response
    ):
        """BDD Scenario PM-1319:
        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1 but is inactive
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing single enrollment's fields data as
        json object nested in a list
        When the user Sends POST Request
        Then the user receives HTTP Response code 404
        And Response Body should contain the error message that the service provider is not active
        """
        factories.ProgramFactory(id=1, program_type=program_type)
        factories.ServiceProviderFactory(id=1, status=ServiceProviderStatus.INACTIVE)
        factories.DerFactory(der_id="test der id")
        resp = client.post("/api/enrollment/", json=[body])
        assert resp.json[0]["status"] == response
        assert "not active" in resp.json[0]["message"]
