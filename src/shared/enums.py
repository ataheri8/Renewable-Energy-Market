from __future__ import annotations

import enum


class ProgramPriority(enum.Enum):
    """Program dispatch priority.
    Lowest to highest
    """

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"


class ControlOptionsEnum(enum.Enum):
    OP_MOD_CONNECT = "OP_MOD_CONNECT"
    OP_MOD_ENERGIZE = "OP_MOD_ENERGIZE"
    OP_MOD_FIXED_PF_ABSORB_W = "OP_MOD_FIXED_PF_ABSORB_W"
    OP_MOD_FIXED_PF_INJECT_W = "OP_MOD_FIXED_PF_INJECT_W"
    OP_MOD_FIXED_VAR = "OP_MOD_FIXED_VAR"
    OP_MOD_FIXED_W = "OP_MOD_FIXED_W"
    OP_MOD_FRED_WATT = "OP_MOD_FRED_WATT"
    OP_MOD_FREQ_DROOP = "OP_MOD_FREQ_DROOP"
    OP_MOD_HFRT_MAY_TRIP = "OP_MOD_HFRT_MAY_TRIP"
    OP_MOD_HFRT_MUST_TRIP = "OP_MOD_HFRT_MUST_TRIP"
    OP_MOD_HVRT_MOMENTARY_CESSATION = "OP_MOD_HVRT_MOMENTARY_CESSATION"
    OP_MOD_HVRT_MUST_TRIP = "OP_MOD_HVRT_MUST_TRIP"
    OP_MOD_LFRT_MAY_TRIP = "OP_MOD_LFRT_MAY_TRIP"
    OP_MOD_LFRT_MUST_TRIP = "OP_MOD_LFRT_MUST_TRIP"
    OP_MOD_LVRT_MAY_TRIP = "OP_MOD_LVRT_MAY_TRIP"
    OP_MOD_LVRT_MOMENTARY_CESSATION = "OP_MOD_LVRT_MOMENTARY_CESSATION"
    OP_MOD_LVRT_MUST_TRIP = "OP_MOD_LVRT_MUST_TRIP"
    OP_MOD_MAX_LIM_W = "OP_MOD_MAX_LIM_W"
    OP_MOD_TARGET_VAR = "OP_MOD_TARGET_VAR"
    OP_MOD_TARGET_W = "OP_MOD_TARGET_W"
    OP_MOD_VOLT_VAR = "OP_MOD_VOLT_VAR"
    OP_MOD_VOLT_WATT = "OP_MOD_VOLT_WATT"
    OP_MOD_WATT_PF = "OP_MOD_WATT_PF"
    OP_MOD_WATT_VAR = "OP_MOD_WATT_VAR"
    RAMP_TMS = "RAMP_TMS"
    CSIP = "CSIP"
    CSIP_AUS = "CSIP_AUS"

    @classmethod
    def get_doe_control_options(cls) -> list[ControlOptionsEnum]:
        return [cls.CSIP, cls.CSIP_AUS]


class ProgramTypeEnum(enum.Enum):
    GENERIC = "GENERIC"
    DYNAMIC_OPERATING_ENVELOPES = "DYNAMIC_OPERATING_ENVELOPES"
    DEMAND_MANAGEMENT = "DEMAND_MANAGEMENT"


class DOEControlType(enum.Enum):
    CONNECTION_POINT_EXPORT_LIMIT = "CONNECTION_POINT_EXPORT_LIMIT"
    CONNECTION_POINT_IMPORT_LIMIT = "CONNECTION_POINT_IMPORT_LIMIT"
    DER_EXPORT_LIMIT = "DER_EXPORT_LIMIT"
    DER_IMPORT_LIMIT = "DER_IMPORT_LIMIT"
