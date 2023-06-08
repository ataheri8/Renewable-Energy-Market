from __future__ import annotations

import enum
from datetime import datetime

import pendulum


class NotificationType(enum.Enum):
    SMS_EMAIL = "SMS_EMAIL"
    CUSTOM_API = "CUSTOM_API"
    OPEN_ADR = "OPEN_ADR"


class ProgramStatus(enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class DispatchLeadTimeEnum(enum.Enum):
    """Options for dispatch lead time.
    Value is in seconds
    """

    TEN_MINS = 600
    THIRTY_MINS = 1800
    ONE_HOUR = 3600
    SIX_HOURS = 21600
    ONE_DAY = 86400


class DispatchTypeEnum(enum.Enum):
    DER_GATEWAY = "DER_GATEWAY"
    API = "API"
    OTHER = "OTHER"


class ProgramTimePeriod(enum.Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"
    PROGRAM_DURATION = "PROGRAM_DURATION"

    @staticmethod
    def get_timestamps_for_periods(
        until_dt: datetime, program_start: datetime
    ) -> dict[ProgramTimePeriod, datetime]:
        pendulum_dt = pendulum.instance(until_dt)
        return {
            ProgramTimePeriod.DAY: pendulum_dt.start_of("day"),
            ProgramTimePeriod.WEEK: pendulum_dt.start_of("week"),
            ProgramTimePeriod.MONTH: pendulum_dt.start_of("month"),
            ProgramTimePeriod.YEAR: pendulum_dt.start_of("year"),
            ProgramTimePeriod.PROGRAM_DURATION: program_start,
        }


class ProgramCategory(enum.Enum):
    LIMIT_BASED = "LIMIT_BASED"
    TARGET_BASED = "TARGET_BASED"
    GENERIC = "GENERIC"


class AvailabilityType(enum.Enum):
    ALWAYS_AVAILABLE = "ALWAYS_AVAILABLE"
    SERVICE_WINDOWS = "SERVICE_WINDOWS"


class ProgramOrderBy(enum.Enum):
    CREATED_AT = "CREATED_AT"
    PROGRAM_TYPE = "PROGRAM_TYPE"
    NAME = "NAME"
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"


class OrderType(enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class DOELimitType(enum.Enum):
    REAL_POWER = "REAL_POWER"
    REACTIVE_POWER = "REACTIVE_POWER"


class DOECalculationFrequency(enum.Enum):
    EVERY_5_MINUTES = "EVERY_5_MINUTES"
    EVERY_15_MINUTES = "EVERY_15_MINUTES"
    EVERY_30_MINUTES = "EVERY_30_MINUTES"
    HOURLY = "HOURLY"
    DAILY = "DAILY"


class ScheduleTimeperiod(enum.Enum):
    MINUTES = "MINUTES"
    HOURS = "HOURS"
    DAYS = "DAYS"


class EnergyUnit(enum.Enum):
    KWH = "KWH"
    MWH = "MWH"
