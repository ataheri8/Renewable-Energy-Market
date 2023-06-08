from pm.modules.enrollment.services.eligibility.criteria_check.base import (
    AbstractCriteriaCheck,
)
from pm.modules.enrollment.services.eligibility.criteria_check.real_power import (
    MaxRealPowerCheck,
    MinRealPowerCheck,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria


def get_criteria_checks(criteria: ResourceEligibilityCriteria) -> list[AbstractCriteriaCheck]:
    criteria_checks: list[AbstractCriteriaCheck] = list()
    if criteria.max_real_power_rating is not None:
        criteria_checks.append(MaxRealPowerCheck())
    if criteria.min_real_power_rating is not None:
        criteria_checks.append(MinRealPowerCheck())
    return criteria_checks
