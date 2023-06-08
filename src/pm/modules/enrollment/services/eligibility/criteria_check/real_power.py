from pm.modules.derinfo.enums import LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.services.eligibility.criteria_check.base import (
    AbstractCriteriaCheck,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria


class MaxRealPowerCheck(AbstractCriteriaCheck):
    def check_eligibility_data_exists(self, der: DerInfo) -> bool:
        if der.nameplate_rating_unit in LimitUnitType.real_power_units():
            return True
        return False

    def check_if_der_eligible(self, criteria: ResourceEligibilityCriteria, der: DerInfo) -> bool:
        if (
            criteria.max_real_power_rating  # type: ignore
            < der.nameplate_rating  # type: ignore
            * LimitUnitType.kw_conversion(der.nameplate_rating_unit)  # type: ignore
        ):
            return False
        return True


class MinRealPowerCheck(AbstractCriteriaCheck):
    def check_eligibility_data_exists(self, der: DerInfo) -> bool:
        if der.nameplate_rating_unit in LimitUnitType.real_power_units():
            return True
        return False

    def check_if_der_eligible(self, criteria: ResourceEligibilityCriteria, der: DerInfo) -> bool:
        if (
            criteria.min_real_power_rating  # type: ignore
            > der.nameplate_rating  # type: ignore
            * LimitUnitType.kw_conversion(der.nameplate_rating_unit)  # type: ignore
        ):
            return False
        return True
