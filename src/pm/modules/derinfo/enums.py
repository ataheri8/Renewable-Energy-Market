from __future__ import annotations

import enum
from typing import Optional


class LimitUnitType(enum.Enum):
    kW = "kW"
    kVAr = "kVAr"
    MW = "MW"
    MVAr = "MVAr"
    V = "V"
    A = "A"
    PF = "PF"
    kWh = "kWh"
    MWh = "MWh"
    kVArh = "kVArh"
    MVArh = "MVArh"
    load_factor = "load_factor"
    F = "F"

    @staticmethod
    def real_power_units() -> list[LimitUnitType]:
        return [LimitUnitType.kW, LimitUnitType.MW]

    @staticmethod
    def kw_conversion(unit: LimitUnitType) -> Optional[float]:
        conversion_dict = dict({LimitUnitType.kW: 1, LimitUnitType.MW: 1000})
        return conversion_dict[unit]


class DerAssetType(enum.Enum):
    DR = "DR"
    BESS = "BESS"
    EV_CHRG_STN = "EV_CHRG_STN"
    PV = "PV"
    WIND_FARM = "WIND_FARM"
    SYNC_GEN = "SYNC_GEN"


class DerResourceCategory(enum.Enum):
    CNI = "CNI"
    GENERIC = "GENERIC"
    RES = "RES"
    UTIL = "UTIL"
    VPP = "VPP"
