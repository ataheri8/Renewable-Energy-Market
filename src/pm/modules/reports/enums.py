from __future__ import annotations

import enum


class ReportTypeEnum(enum.Enum):
    INDIVIDUAL_PROGRAM = "INDIVIDUAL_PROGRAM"
    INDIVIDUAL_SERVICE_PROVIDER = "INDIVIDUAL_SERVICE_PROVIDER"


class OrderType(enum.Enum):
    ASC = "ASC"
    DESC = "DESC"
