import pytest

from pm.modules.enrollment.services.eligibility.criteria_check import (
    MaxRealPowerCheck,
    MinRealPowerCheck,
    get_criteria_checks,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria


class TestInitCriteriaCheck:
    @pytest.mark.parametrize(
        "min_power,max_power,length",
        [
            pytest.param(
                None,
                None,
                0,
                id="empty-criteria-checks",
            ),
            pytest.param(
                10,
                None,
                1,
                id="only-min-criteria-checks",
            ),
            pytest.param(
                None,
                1000,
                1,
                id="only-max-criteria-checks",
            ),
            pytest.param(
                10,
                1000,
                2,
                id="min-and-max-criteria-checks",
            ),
        ],
    )
    def test_get_criteria_checks(self, min_power, max_power, length):
        criteria = ResourceEligibilityCriteria(
            min_real_power_rating=min_power, max_real_power_rating=max_power
        )
        checks = get_criteria_checks(criteria)
        assert len(checks) == length
        for check in checks:
            if isinstance(check, MinRealPowerCheck):
                assert min_power is not None
            if isinstance(check, MaxRealPowerCheck):
                assert max_power is not None
