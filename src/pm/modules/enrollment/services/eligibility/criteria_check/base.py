from abc import ABC, abstractmethod
from typing import Optional

from pm.modules.enrollment.enums import EnrollmentRejectionReason
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.modules.serviceprovider.models import DerInfo


class AbstractCriteriaCheck(ABC):
    @abstractmethod
    def check_eligibility_data_exists(self, der: DerInfo) -> bool:
        """
        Use this function to check if the DER has the required fields populated in order
        to do the criteria check. Return True if we can proceed with the check, False otherwise.
        """

    @abstractmethod
    def check_if_der_eligible(self, criteria: ResourceEligibilityCriteria, der: DerInfo) -> bool:
        """
        Use this function to do the actual criteria check. You can assume the DER has the required
        data to do the check. Return True if the DER is eligible for the program, False otherwise.
        """

    def criteria_check(
        self, criteria: ResourceEligibilityCriteria, der: DerInfo
    ) -> Optional[EnrollmentRejectionReason]:
        if not self.check_eligibility_data_exists(der):
            return EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND
        if not self.check_if_der_eligible(criteria, der):
            return EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA
        return None
