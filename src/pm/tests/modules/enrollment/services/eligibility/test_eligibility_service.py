import pytest

from pm.modules.derinfo.enums import LimitUnitType
from pm.modules.enrollment.enums import (
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.enrollment.services.eligibility.eligibility import EligibilityService
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.tests import factories


class TestEligibilityService:
    def test_eligibility_check_der_not_associated(self):
        program = factories.Program()
        der = factories.DerInfo()
        enrollment_request = factories.EnrollmentRequest(service_provider_id=1)
        status, reason = EligibilityService().eligibility_check(program, der, enrollment_request)
        assert status == EnrollmentRequestStatus.REJECTED
        assert reason == EnrollmentRejectionReason.DER_NOT_ASSOCIATED_WITH_SERVICE_PROVIDER

    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit",
        [
            pytest.param(0, LimitUnitType.kW),
            pytest.param(100, LimitUnitType.V),
            pytest.param(10, LimitUnitType.kVArh),
            pytest.param(-100, LimitUnitType.A),
        ],
    )
    def test_eligibility_check_no_check(self, nameplate_rating, nameplate_rating_unit):
        program = factories.Program(check_der_eligibility=False)
        der = factories.DerInfo(
            nameplate_rating=nameplate_rating, nameplate_rating_unit=nameplate_rating_unit
        )
        enrollment_request = factories.EnrollmentRequest()
        status, reason = EligibilityService().eligibility_check(program, der, enrollment_request)
        assert status == EnrollmentRequestStatus.ACCEPTED
        assert reason is None

    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit",
        [
            pytest.param(0, LimitUnitType.MW),
            pytest.param(100, LimitUnitType.load_factor),
            pytest.param(10, LimitUnitType.PF),
            pytest.param(-100, LimitUnitType.F),
        ],
    )
    def test_eligibility_check_no_criteria(self, nameplate_rating, nameplate_rating_unit):
        program = factories.Program(
            check_der_eligibility=True, resource_eligibility_criteria=ResourceEligibilityCriteria()
        )

        der = factories.DerInfo(
            nameplate_rating=nameplate_rating,
            nameplate_rating_unit=nameplate_rating_unit,
            service_provider_id=1,
        )
        enrollment_request = factories.EnrollmentRequest(service_provider_id=1)
        status, reason = EligibilityService().eligibility_check(program, der, enrollment_request)
        assert reason is None
        assert status == EnrollmentRequestStatus.ACCEPTED

    @pytest.mark.parametrize(
        "criteria,nameplate_rating,nameplate_rating_unit,exp_status,exp_reason",
        [
            pytest.param(
                ResourceEligibilityCriteria(),
                1,
                LimitUnitType.kVArh,
                EnrollmentRequestStatus.ACCEPTED,
                None,
                id="No-criteria-missing-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(),
                100,
                LimitUnitType.kW,
                EnrollmentRequestStatus.ACCEPTED,
                None,
                id="No-criteria-populated-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(min_real_power_rating=100),
                10,
                LimitUnitType.kW,
                EnrollmentRequestStatus.REJECTED,
                EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA,
                id="1-criteria-bad-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(min_real_power_rating=100),
                1000,
                LimitUnitType.MW,
                EnrollmentRequestStatus.ACCEPTED,
                None,
                id="1-criteria-valid-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(min_real_power_rating=100),
                1000,
                LimitUnitType.kVAr,
                EnrollmentRequestStatus.REJECTED,
                EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND,
                id="1-criteria-missing-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(min_real_power_rating=100, max_real_power_rating=1000),
                10000,
                LimitUnitType.kW,
                EnrollmentRequestStatus.REJECTED,
                EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA,
                id="2-criteria-bad-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(min_real_power_rating=100, max_real_power_rating=1000),
                1,
                LimitUnitType.MW,
                EnrollmentRequestStatus.ACCEPTED,
                None,
                id="2-criteria-valid-name-plate-rating",
            ),
            pytest.param(
                ResourceEligibilityCriteria(min_real_power_rating=100, max_real_power_rating=1000),
                500,
                LimitUnitType.kVArh,
                EnrollmentRequestStatus.REJECTED,
                EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND,
                id="2-criteria-missing-name-plate-rating",
            ),
        ],
    )
    def test_eligibility_check_with_criteria(
        self, criteria, nameplate_rating, nameplate_rating_unit, exp_status, exp_reason
    ):
        program = factories.Program(
            check_der_eligibility=True, resource_eligibility_criteria=criteria
        )
        der = factories.DerInfo(
            nameplate_rating=nameplate_rating,
            nameplate_rating_unit=nameplate_rating_unit,
            service_provider_id=1,
        )
        enrollment_request = factories.EnrollmentRequest(service_provider_id=1)
        status, reason = EligibilityService().eligibility_check(program, der, enrollment_request)
        assert status == exp_status
        assert reason is exp_reason
