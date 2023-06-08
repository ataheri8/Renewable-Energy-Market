from pm.modules.enrollment.enums import EnrollmentRejectionReason
from pm.modules.enrollment.services.eligibility.criteria_check import (
    AbstractCriteriaCheck,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.modules.serviceprovider.models import DerInfo


class TestCriteriaCheckMissingEligibility(AbstractCriteriaCheck):
    def check_eligibility_data_exists(self, der: DerInfo) -> bool:
        return False

    def check_if_der_eligible(self, criteria: ResourceEligibilityCriteria, der: DerInfo) -> bool:
        return True


class TestCriteriaCheckNotEligible(AbstractCriteriaCheck):
    def check_eligibility_data_exists(self, der: DerInfo) -> bool:
        return True

    def check_if_der_eligible(self, criteria: ResourceEligibilityCriteria, der: DerInfo) -> bool:
        return False


class TestCriteriaCheckIsEligible(AbstractCriteriaCheck):
    def check_eligibility_data_exists(self, der: DerInfo) -> bool:
        return True

    def check_if_der_eligible(self, criteria: ResourceEligibilityCriteria, der: DerInfo) -> bool:
        return True


class TestAbstractCriteriaClass:
    def test_eligibility_data_does_not_exist(self):
        der = DerInfo()
        criteria = ResourceEligibilityCriteria()
        check = TestCriteriaCheckMissingEligibility()
        assert (
            check.criteria_check(criteria, der)
            == EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND
        )

    def test_der_not_eligible(self):
        der = DerInfo()
        criteria = ResourceEligibilityCriteria()
        check = TestCriteriaCheckNotEligible()
        assert (
            check.criteria_check(criteria, der)
            == EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA
        )

    def test_test_is_eligible(self):
        der = DerInfo()
        criteria = ResourceEligibilityCriteria()
        check = TestCriteriaCheckIsEligible()
        assert check.criteria_check(criteria, der) is None
