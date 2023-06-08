from http import HTTPStatus

import pytest

from pm.modules.derinfo.enums import LimitUnitType
from pm.modules.enrollment.enums import (
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.tests import factories
from pm.tests_acceptance.enrollment.mixins import EnrollmentMixin


class TestPM286(EnrollmentMixin):
    """[PMM Enrollment] DER Internal Eligibility Check"""

    def test_eligibility_check_pass(self, client, db_session):
        """
        BDD Scenario PM-287
        Given a DER fits the eligibility criteria for a program
        When an enrollment request is created for that DER into that program
        Then the enrollment status is set to ACCEPTED
        """
        program = factories.ProgramFactory(
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory()
        # der with power rating between 100 and 10000 kW
        der = factories.DerFactory(
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

        # check there is a contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) > 0
        assert resp.json[0]["enrollment_request_id"] == 1
        assert resp.json[0]["der_id"] == der_id

    def test_eligibility_check_fail(self, client, db_session):
        """
        BDD Scenario PM-288
        Given a DER does not fit the eligibility criteria for a program
        When an enrollment request is created for that DER into that program
        Then the enrollment status is set to REJECTED
            And the rejection reason is set as DER_DOES_NOT_MEET_CRITERIA
        """
        program = factories.ProgramFactory(
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory()
        # der with power rating over than 10000 kW (10 MW)
        der = factories.DerFactory(
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

        # check there is no contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 0

    # Integration test for BDD PM-724
    def test_eligibility_check_no_criteria(self, client, db_session):
        """
        BDD Scenario PM-289
        Given there is no eligibility criteria for a program
            And a DER exists in DER Warehouse
        When an enrollment request is created for that DER into that program
        Then the enrollment status is set to ACCEPTED
        """
        program = factories.ProgramFactory(
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(),
        )
        service_provider = factories.ServiceProviderFactory()
        # der with any rating
        der = factories.DerFactory(
            nameplate_rating=1,
            nameplate_rating_unit=LimitUnitType.kVAr,
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

        # check there is a contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) > 0
        assert resp.json[0]["enrollment_request_id"] == 1
        assert resp.json[0]["der_id"] == der_id

    # Integration test for BDD PM-725
    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit",
        [
            pytest.param(100, LimitUnitType.A),
            pytest.param(100, LimitUnitType.V),
            pytest.param(100, LimitUnitType.kVAr),
            pytest.param(100, LimitUnitType.kVArh),
        ],
    )
    def test_eligibility_check_der_criteria_data_missing(
        self, client, db_session, nameplate_rating, nameplate_rating_unit
    ):
        """
        BDD Scenario PM-290
        Given a program has eligibility criteria
            And the DER data for that criteria doesn't exist in DER Warehouse
        When an enrollment request is created for that DER into that program
        Then the enrollment status is set to REJECTED
            And the rejection reason is set as ELIGIBILITY_DATA_NOT_FOUND
        """
        program = factories.ProgramFactory(
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory()
        # der with power rating missing
        der = factories.DerFactory(
            nameplate_rating=nameplate_rating,
            nameplate_rating_unit=nameplate_rating_unit,
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
        assert enrollment.rejection_reason == EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND

        # check there is no contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 0

    def test_eligibility_check_der_not_found(self, client, db_session):
        """
        BDD Scenario PM-291
        Given a DER does not exist ins DER Warehouse
        When an enrollment request is created for that DER into any program
        Then the enrollment status is set to REJECTED
            And the rejection reason is set as DER_NOT_FOUND
        """
        program = factories.ProgramFactory(
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory()

        der_id = "fake_id"
        body = self._get_enrollment_body(program.id, service_provider.id, der_id)
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "NOT_CREATED"

    def test_eligibility_check_der_not_associated(
        self,
        client,
        db_session,
    ):
        """
        BDD Scenario PM-291
        Given a DER exists but is not associated with the correct service provider
        When an enrollment request is created for that DER and a different service provider
            into any program
        Then the enrollment status is set to REJECTED
            And the rejection reason is set as DER_NOT_ASSOCIATED_WITH_SERVICE_PROVIDER
        """
        program = factories.ProgramFactory(
            check_der_eligibility=True,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                max_real_power_rating=10000, min_real_power_rating=100
            ),
        )
        service_provider = factories.ServiceProviderFactory()

        der = factories.DerFactory(service_provider_id=None)

        body = self._get_enrollment_body(program.id, service_provider.id, der.der_id)
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "CREATED"
        enrollment_request_id = resp.json[0]["id"]
        enrollment = self._get_enrollment_request_from_db(db_session, enrollment_request_id)
        assert enrollment is not None
        assert enrollment.enrollment_status == EnrollmentRequestStatus.REJECTED
        assert (
            enrollment.rejection_reason
            == EnrollmentRejectionReason.DER_NOT_ASSOCIATED_WITH_SERVICE_PROVIDER
        )

        # check there is no contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 0

    def test_eligibility_check_external(self, client, db_session):
        """
        BDD Scenario PM-603
        Given the eligibility check for a program is set to external
            And a DER exists in DER Warehouse
        When an enrollment request is created for that DER into that program
        Then the enrollment status is set to ACCEPTED
        """
        program = factories.ProgramFactory(
            check_der_eligibility=False,
            resource_eligibility_criteria=ResourceEligibilityCriteria(),
        )
        service_provider = factories.ServiceProviderFactory()
        # der with any power rating
        der = factories.DerFactory(
            nameplate_rating=1,
            nameplate_rating_unit=LimitUnitType.kVAr,
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

        # check there is a contract in the system
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) > 0
        assert resp.json[0]["enrollment_request_id"] == 1
        assert resp.json[0]["der_id"] == der_id
