from typing import Optional

from pm.modules.enrollment.enums import (
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.enrollment.models import EnrollmentRequest
from pm.modules.enrollment.services.eligibility.criteria_check import (
    get_criteria_checks,
)
from pm.modules.progmgmt.models import Program
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.modules.serviceprovider.models import DerInfo


class EligibilityService:
    def eligibility_check(
        self,
        program: Program,
        der: DerInfo,
        enrollment_request: EnrollmentRequest,
    ) -> tuple[EnrollmentRequestStatus, Optional[EnrollmentRejectionReason]]:
        if der.service_provider_id != enrollment_request.service_provider_id:
            return (
                EnrollmentRequestStatus.REJECTED,
                EnrollmentRejectionReason.DER_NOT_ASSOCIATED_WITH_SERVICE_PROVIDER,
            )
        elif not program.check_der_eligibility or not program.resource_eligibility_criteria:
            return EnrollmentRequestStatus.ACCEPTED, None
        else:
            return self._check_eligibility_criteria(program.resource_eligibility_criteria, der)

    def _check_eligibility_criteria(
        self, criteria: ResourceEligibilityCriteria, der: DerInfo
    ) -> tuple[EnrollmentRequestStatus, Optional[EnrollmentRejectionReason]]:
        criteria_checks = get_criteria_checks(criteria)
        for check in criteria_checks:
            rejection_reason = check.criteria_check(criteria, der)
            if rejection_reason is not None:
                return EnrollmentRequestStatus.REJECTED, rejection_reason

        return EnrollmentRequestStatus.ACCEPTED, None
