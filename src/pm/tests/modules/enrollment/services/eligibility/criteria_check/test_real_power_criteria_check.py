import pytest

from pm.modules.derinfo.enums import LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.services.eligibility.criteria_check import (
    MaxRealPowerCheck,
    MinRealPowerCheck,
)
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria


class TestMaxRealPowerCheck:
    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit,result",
        [
            pytest.param(
                100,
                LimitUnitType.kVAr,
                False,
                id="der-criteria-missing-type",
            ),
            pytest.param(
                0,
                LimitUnitType.kW,
                True,
                id="der-criteria-zero",
            ),
            pytest.param(
                10,
                LimitUnitType.MW,
                True,
                id="der-criteria-non-zero",
            ),
        ],
    )
    def test_check_eligibility_data_exists_max_power(
        self, nameplate_rating, nameplate_rating_unit, result
    ):
        der = DerInfo(
            nameplate_rating=nameplate_rating, nameplate_rating_unit=nameplate_rating_unit
        )
        assert MaxRealPowerCheck().check_eligibility_data_exists(der) == result

    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit,max_rating,result",
        [
            pytest.param(
                10.23,
                LimitUnitType.kW,
                100,
                True,
                id="success-kw",
            ),
            pytest.param(
                1.005,
                LimitUnitType.MW,
                10000,
                True,
                id="success-mw",
            ),
            pytest.param(
                100.50,
                LimitUnitType.kW,
                100.50,
                True,
                id="exactly-equal-success",
            ),
            pytest.param(
                1000.23,
                LimitUnitType.kW,
                100,
                False,
                id="fail-kw",
            ),
            pytest.param(
                10.320,
                LimitUnitType.MW,
                100,
                False,
                id="fail-mw",
            ),
        ],
    )
    def test_check_if_der_eligible_max_power(
        self, nameplate_rating, nameplate_rating_unit, max_rating, result
    ):
        der = DerInfo(
            nameplate_rating=nameplate_rating, nameplate_rating_unit=nameplate_rating_unit
        )
        criteria = ResourceEligibilityCriteria(max_real_power_rating=max_rating)
        assert MaxRealPowerCheck().check_if_der_eligible(criteria, der) == result


class TestMinRealPowerCheck:
    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit,result",
        [
            pytest.param(
                100,
                LimitUnitType.kVAr,
                False,
                id="der-criteria-missing-type",
            ),
            pytest.param(
                0,
                LimitUnitType.kW,
                True,
                id="der-criteria-zero",
            ),
            pytest.param(
                10,
                LimitUnitType.MW,
                True,
                id="der-criteria-non-zero",
            ),
        ],
    )
    def test_check_eligibility_data_exists_min_power(
        self, nameplate_rating, nameplate_rating_unit, result
    ):
        der = DerInfo(
            nameplate_rating=nameplate_rating, nameplate_rating_unit=nameplate_rating_unit
        )
        assert MinRealPowerCheck().check_eligibility_data_exists(der) == result

    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit,min_rating,result",
        [
            pytest.param(
                1000,
                LimitUnitType.kW,
                100,
                True,
                id="success-kw",
            ),
            pytest.param(
                10,
                LimitUnitType.MW,
                1000,
                True,
                id="success-mw",
            ),
            pytest.param(
                100,
                LimitUnitType.kW,
                100,
                True,
                id="exactly-equal-success",
            ),
            pytest.param(
                100,
                LimitUnitType.kW,
                1000,
                False,
                id="fail-kw",
            ),
            pytest.param(
                1,
                LimitUnitType.MW,
                10000,
                False,
                id="fail-mw",
            ),
        ],
    )
    def test_check_if_der_eligible_min_power(
        self, nameplate_rating, nameplate_rating_unit, min_rating, result
    ):
        der = DerInfo(
            nameplate_rating=nameplate_rating, nameplate_rating_unit=nameplate_rating_unit
        )
        criteria = ResourceEligibilityCriteria(min_real_power_rating=min_rating)
        assert MinRealPowerCheck().check_if_der_eligible(criteria, der) == result
