from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from shared.enums import (
    ControlOptionsEnum,
    DOEControlType,
    ProgramPriority,
    ProgramTypeEnum,
)
from shared.system import loggingsys

logger = loggingsys.get_logger(__name__)

# Shared validation for DER Gateway Program messages
# This is used by the DER Gateway Relay and Program Manager


@dataclass
class _HolidayEvents(DataClassJsonMixin):
    startDate: str
    endDate: str
    name: str
    category: str
    substitutionDate: Optional[str] = None


@dataclass
class _HolidayCalendars(DataClassJsonMixin):
    mrid: str
    timezone: str
    year: int
    events: list[_HolidayEvents]


@dataclass
class _HolidayExclusions(DataClassJsonMixin):
    calendars: list[_HolidayCalendars]


@dataclass
class _MinMax(DataClassJsonMixin):
    min: Optional[float] = None
    max: Optional[float] = None


@dataclass
class _DispatchConstraints(DataClassJsonMixin):
    event_duration_constraint: _MinMax
    cumulative_event_duration: dict[str, _MinMax]
    max_number_of_events_per_timeperiod: dict[str, int]


@dataclass
class _AvailServiceWindows(DataClassJsonMixin):
    id: int
    start_hour: int
    end_hour: int
    mon: bool
    tue: bool
    wed: bool
    thu: bool
    fri: bool
    sat: bool
    sun: bool


@dataclass
class _AvailOperatingMonths(DataClassJsonMixin):
    id: int
    jan: bool
    feb: bool
    mar: bool
    apr: bool
    may: bool
    jun: bool
    jul: bool
    aug: bool
    sep: bool
    oct: bool
    nov: bool
    dec: bool


@dataclass
class _DemandManagementConstraints(DataClassJsonMixin):
    max_total_energy_per_timeperiod: int
    max_total_energy_unit: str
    timeperiod: str


DEFAULT_END_DATE = "2099-12-31 00:00:00.00+00:00"


@dataclass
class Program(DataClassJsonMixin):
    id: int
    name: str
    program_type: ProgramTypeEnum
    start_date: str
    end_date: str = field(default_factory=lambda: DEFAULT_END_DATE)
    program_priority: Optional[ProgramPriority] = ProgramPriority.P0
    avail_operating_months: Optional[_AvailOperatingMonths] = None
    holiday_exclusions: Optional[_HolidayExclusions] = None
    control_type: Optional[list[DOEControlType]] = field(default_factory=list[DOEControlType])
    control_options: Optional[list[ControlOptionsEnum]] = field(
        default_factory=list[ControlOptionsEnum]
    )
    dispatch_constraints: Optional[_DispatchConstraints] = None
    avail_service_windows: Optional[list[_AvailServiceWindows]] = None

    demand_management_constraints: Optional[_DemandManagementConstraints] = None


@dataclass
class Contract(DataClassJsonMixin):
    id: int
    contract_type: str


@dataclass
class Enrollment(DataClassJsonMixin):
    der_id: str


@dataclass
class DerGatewayProgram(DataClassJsonMixin):
    program: Program
    contract: Contract
    enrollment: Enrollment
