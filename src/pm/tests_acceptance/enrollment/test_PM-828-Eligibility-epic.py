from http import HTTPStatus

from pm.modules.derinfo.enums import LimitUnitType
from pm.modules.enrollment.enums import (
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.tests import factories
from pm.tests_acceptance.enrollment.mixins import EnrollmentMixin


class TestPM828(EnrollmentMixin):
    """[PMM Enrollment] DER Internal Eligibility Check Epic"""

    def test_eligibility_check_pass_and_report(self, client, db_session):
        """
        BDD Scenario PM-829
        Given a program and DER exist in the database
        And the DER meets the eligibility criteria for the program
        When the enrollment request is created through the api
        And the eligibility check completes
        And the enrollment report is requested for that program
        Then the enrollment request details will be found in the report
        And the enrollment status will say ACCEPTED
        And the rejection reason will be blank
        """
        program = factories.ProgramFactory(
            id=1,
            name="Program Success",
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory(id=1)
        # der with power rating between 100 and 10000 kW
        der = factories.DerFactory(
            der_id="der_success",
            nameplate_rating=200,
            nameplate_rating_unit=LimitUnitType.kW,
            service_provider_id=service_provider.id,
        )
        der_id = der.der_id

        body = self._get_enrollment_body(program.id, service_provider.id, der.der_id)
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "CREATED"
        enrollment_request_id = resp.json[0]["id"]
        enrollment = self._get_enrollment_request_from_db(db_session, enrollment_request_id)
        assert enrollment is not None
        assert enrollment.enrollment_status == EnrollmentRequestStatus.ACCEPTED
        enrollment_created_at = enrollment.created_at.isoformat()

        # check there is a contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) > 0
        assert resp.json[0]["enrollment_request_id"] == 1
        assert resp.json[0]["der_id"] == der_id

        # check enrollment request shows up in report correctly
        expected_report = (
            "Program Name,DER ID,Service Provider ID,Enrollment Time,"
            "Enrollment User ID,Enrollment Status,Rejection Reason\r\n"
            f"Program Success,der_success,1,{enrollment_created_at},,"
            "ACCEPTED,\r\n"
        )
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.data.decode("utf-8") == expected_report

    def test_eligibility_check_fail_and_report(self, client, db_session):
        """
        BDD Scenario PM-838
        Given a program and DER exist in the database
        And the DER does not meet the eligibility criteria for the program
        When the enrollment request is created through the api
        And the eligibility check completes
        And the enrollment report is requested for that program
        Then the enrollment request details will be found in the report
        And the enrollment status will say REJECTED
        And the rejection reason will be th plain text representation of the reason it was rejected
        """
        program = factories.ProgramFactory(
            id=1,
            name="Program Failure",
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory(id=1)
        # der with power rating over than 10000 kW (10 MW)
        der = factories.DerFactory(
            der_id="der_failure",
            nameplate_rating=200,
            nameplate_rating_unit=LimitUnitType.MW,
            service_provider_id=service_provider.id,
        )
        body = self._get_enrollment_body(program.id, service_provider.id, der.der_id)
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "CREATED"
        enrollment_request_id = resp.json[0]["id"]
        enrollment = self._get_enrollment_request_from_db(db_session, enrollment_request_id)
        assert enrollment is not None
        assert enrollment.enrollment_status == EnrollmentRequestStatus.REJECTED
        assert enrollment.rejection_reason == EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA
        enrollment_created_at = enrollment.created_at.isoformat()

        # check there is no contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 0

        # check enrollment request shows up in report correctly
        expected_report = (
            "Program Name,DER ID,Service Provider ID,Enrollment Time,"
            "Enrollment User ID,Enrollment Status,Rejection Reason\r\n"
            f"Program Failure,der_failure,1,{enrollment_created_at},,"
            "REJECTED,DER does not meet the program criteria\r\n"
        )
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.data.decode("utf-8") == expected_report
