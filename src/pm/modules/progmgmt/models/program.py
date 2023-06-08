from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict

import pendulum
from dataclasses_json import DataClassJsonMixin
from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.sqltypes import Boolean

from pm.modules.progmgmt.enums import (
    AvailabilityType,
    DispatchTypeEnum,
    DOECalculationFrequency,
    DOELimitType,
    EnergyUnit,
    NotificationType,
    ProgramCategory,
    ProgramStatus,
    ProgramTimePeriod,
    ScheduleTimeperiod,
)
from shared.enums import (
    ControlOptionsEnum,
    DOEControlType,
    ProgramPriority,
    ProgramTypeEnum,
)
from shared.exceptions import Error
from shared.model import (
    CreatedAtUpdatedAtMixin,
    DataclassJSONB,
    EnumListJSONB,
    make_enum,
    make_timestamptz,
)
from shared.system.database import Base
from shared.system.loggingsys import get_logger

from .avail_operating_months import AvailOperatingMonths
from .avail_service_window import AvailServiceWindow
from .dispatch_notification import DispatchNotification
from .dispatch_opt_out import DispatchOptOut

logger = get_logger(__name__)


@dataclass
class MinMax:
    min: Optional[int] = None
    max: Optional[int] = None


@dataclass
class Constraints(DataClassJsonMixin):
    """Dispatch constraints
    cumulative_event_duration & max_number_of_events_per_timeperiod keys are ProgramTimePeriod name
    """

    event_duration_constraint: Optional[MinMax] = None
    cumulative_event_duration: Optional[dict[str, MinMax]] = None
    max_number_of_events_per_timeperiod: Optional[dict[str, int]] = None


@dataclass
class DemandManagementConstraints(DataClassJsonMixin):
    max_total_energy_per_timeperiod: Optional[float] = None
    max_total_energy_unit: Optional[EnergyUnit] = None
    timeperiod: Optional[ProgramTimePeriod] = None


@dataclass
class ResourceEligibilityCriteria(DataClassJsonMixin):
    max_real_power_rating: Optional[float] = None
    min_real_power_rating: Optional[float] = None


@dataclass
class HolidayCalendarsDict:
    calendars: list[HolidayCalendarInfoDict]

    def __getitem__(self, args):
        return self.calendars


class Program(CreatedAtUpdatedAtMixin, Base):
    """Base class for programs. The program table implements single table inheritance.
    https://docs.sqlalchemy.org/en/20/orm/inheritance.html#single-table-inheritance

    Programs share attributes, but not all programs will have all attributes.
    The attributes are updated in the subclasses, and the type of subclass is determined
    by the program_type column.
    """

    __tablename__ = "program"
    # the polymorphic_on column is used to determine the type of program
    __mapper_args__: dict = {"polymorphic_on": "program_type"}

    id: int = Column(Integer, primary_key=True)
    name: str = Column(UnicodeText, nullable=True)
    program_type: ProgramTypeEnum = Column(make_enum(ProgramTypeEnum), nullable=False)
    program_category: Optional[ProgramCategory] = Column(make_enum(ProgramCategory), nullable=True)
    start_date: Optional[datetime] = Column(make_timestamptz(), nullable=True)
    end_date: Optional[datetime] = Column(make_timestamptz(), nullable=True)
    program_priority: Optional[ProgramPriority] = Column(make_enum(ProgramPriority), nullable=True)
    availability_type: Optional[AvailabilityType] = Column(
        make_enum(AvailabilityType), nullable=True
    )
    notification_type: Optional[NotificationType] = Column(
        make_enum(NotificationType), nullable=True
    )
    resource_eligibility_criteria: Optional[ResourceEligibilityCriteria] = Column(
        DataclassJSONB(ResourceEligibilityCriteria), nullable=True
    )
    holiday_exclusions: Optional[HolidayCalendarsDict] = Column(JSONB, nullable=True)
    check_der_eligibility: Optional[bool] = Column(Boolean, nullable=True)
    define_contractual_target_capacity: Optional[bool] = Column(Boolean, nullable=True)
    dispatch_constraints: Optional[Constraints] = Column(DataclassJSONB(Constraints), nullable=True)
    demand_management_constraints: Optional[DemandManagementConstraints] = Column(
        DataclassJSONB(DemandManagementConstraints), nullable=True
    )
    status: Optional[ProgramStatus] = Column(
        make_enum(ProgramStatus), default=ProgramStatus.DRAFT, nullable=False
    )
    limit_type: Optional[DOELimitType] = Column(make_enum(DOELimitType), nullable=True)
    control_type: Optional[list[DOEControlType]] = Column(
        EnumListJSONB(DOEControlType), nullable=True
    )
    calculation_frequency: Optional[DOECalculationFrequency] = Column(
        make_enum(DOECalculationFrequency), nullable=True
    )
    schedule_time_horizon_timeperiod: Optional[ScheduleTimeperiod] = Column(
        make_enum(ScheduleTimeperiod), nullable=True
    )
    schedule_time_horizon_number: Optional[int] = Column(Integer, nullable=True)
    schedule_timestep_mins: Optional[int] = Column(Integer, nullable=True)
    control_options: Optional[list[ControlOptionsEnum]] = Column(
        EnumListJSONB(ControlOptionsEnum), nullable=True
    )
    dispatch_type: Optional[DispatchTypeEnum] = Column(make_enum(DispatchTypeEnum), nullable=True)
    track_event: Optional[bool] = Column(Boolean, nullable=True)
    avail_operating_months: Mapped[AvailOperatingMonths] = relationship(
        "AvailOperatingMonths",
        cascade="all, delete, delete-orphan",
        uselist=False,
        single_parent=True,
    )
    dispatch_max_opt_outs: Mapped[list["DispatchOptOut"]] = relationship(
        "DispatchOptOut",
        cascade="all, delete, delete-orphan",
    )
    dispatch_notifications: Mapped[list["DispatchNotification"]] = relationship(
        "DispatchNotification",
        cascade="all, delete, delete-orphan",
    )
    avail_service_windows: Mapped[list["AvailServiceWindow"]] = relationship(
        "AvailServiceWindow",
        cascade="all, delete, delete-orphan",
    )

    def set_program_status(self, status: ProgramStatus):
        if self.status == ProgramStatus.ARCHIVED:
            raise InvalidProgramStatus("Program is already archived")
        elif status == ProgramStatus.ACTIVE:
            raise InvalidProgramStatus("Programs cannot be manually set to ACTIVE")
        elif self.status and status == ProgramStatus.DRAFT and self.status != ProgramStatus.DRAFT:
            raise InvalidProgramStatus("Programs cannot be moved back to DRAFT")
        else:
            self.status = status

    def _set_start_end_time(self, start: Optional[datetime], end: Optional[datetime]):
        start_time = start if start else self.start_date
        end_time = end if end else self.end_date
        if start_time and end_time and start_time >= end_time:
            logger.error("Invalid program duration, start_date must be before end_date")
            raise InvalidProgramStartEndTimes("start_date must be before end_date")
        self.start_date = start_time
        self.end_date = end_time

    def _update_shared_fields(self, data: CreateUpdateProgram):
        if data.general_fields.start_date or data.general_fields.end_date:
            self._set_start_end_time(data.general_fields.start_date, data.general_fields.end_date)
        self.program_priority = data.general_fields.program_priority or self.program_priority
        self.availability_type = data.general_fields.availability_type or self.availability_type
        self.check_der_eligibility = (
            data.general_fields.check_der_eligibility or self.check_der_eligibility
        )
        self.define_contractual_target_capacity = (
            data.general_fields.define_contractual_target_capacity
            or self.define_contractual_target_capacity
        )
        self.notification_type = data.general_fields.notification_type or self.notification_type
        self.resource_eligibility_criteria = (
            data.resource_eligibility_criteria or self.resource_eligibility_criteria
        )
        if data.avail_operating_months:
            self.avail_operating_months = AvailOperatingMonths.factory(
                data.avail_operating_months
            )  # type: ignore
        if data.dispatch_max_opt_outs is not None:
            self.dispatch_max_opt_outs = DispatchOptOut.bulk_factory(
                data.dispatch_max_opt_outs
            )  # type: ignore
        if data.dispatch_notifications is not None:
            self.dispatch_notifications = DispatchNotification.bulk_factory(
                data.dispatch_notifications
            )  # type: ignore
        if data.avail_service_windows is not None:
            self.avail_service_windows = AvailServiceWindow.bulk_factory(
                data.avail_service_windows
            )  # type: ignore

    def set_name(self, name: str, name_count: int):
        if name_count > 0:
            errors = {"general_fields": {"name": f"{name} is not unique"}}
            logger.error(f"Duplicate programe name, {name} already exists")
            raise ProgramNameDuplicate(message="name already exists", errors=errors)
        self.name = name

    def save_holiday_exclusion_program(self, payload: HolidayCalendarsDict):
        if self.status == ProgramStatus.ARCHIVED:
            logger.error(
                f"Program (ID: {self.id}) is already archived. Unable to save holiday exclusion."
            )
            raise InvalidProgramStatus("Program is already archived")
        self.holiday_exclusions = payload  # type: ignore
        logger.info("Saved holiday exclusion to program")

    def set_program_fields(self, data: CreateUpdateProgram):
        """Validates and sets a program's fields"""
        # program cannot be updated if the end date is reached or if it is archived
        if self.status == ProgramStatus.ARCHIVED:
            logger.error("Program is archived and cannot be updated")
            raise ProgramSaveViolation("Cannot update a program that is archived")
        if self.end_date and self.end_date < pendulum.now():
            logger.error("Cannot update a program that has finished")
            raise ProgramSaveViolation("Cannot update a program that has finished")
        self._update_shared_fields(data)
        self._update_program_specific_fields(data)
        if data.general_fields.status:
            self.set_program_status(data.general_fields.status)
        logger.info(f"Saved Program: \n{data}")

    def _update_program_specific_fields(self, _: CreateUpdateProgram):
        pass

    @classmethod
    def factory(
        self,
        name: str,
        program_type: ProgramTypeEnum,
        name_count: int = 0,
    ) -> Program:
        """Create a Program.
        Requires name and program_type.
        """
        program: Program
        if program_type == ProgramTypeEnum.DEMAND_MANAGEMENT:
            program = DemandManagementProgram(
                name=name,
                program_type=program_type,
                program_category=ProgramCategory.TARGET_BASED,
            )
        elif program_type == ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES:
            program = DynamicOperatingEnvelopesProgram(
                name=name,
                program_type=program_type,
                program_category=ProgramCategory.LIMIT_BASED,
            )
        else:
            program = GenericProgram(
                name=name,
                program_type=program_type,
                program_category=ProgramCategory.GENERIC,
            )
        self.set_name(program, name, name_count)
        logger.info("Created Program")
        return program


class GenericProgram(Program):
    # polymorphic_identity is used by the orm to identify the program type
    __mapper_args__: dict = {"polymorphic_identity": ProgramTypeEnum.GENERIC}

    def _update_program_specific_fields(self, data: CreateUpdateProgram):
        if data.control_options is not None:
            self.control_options = data.control_options
        if data.dispatch_type is not None:
            self.dispatch_type = data.dispatch_type
        if data.track_event is not None:
            self.track_event = data.track_event
        self.dispatch_constraints = data.dispatch_constraints or self.dispatch_constraints


class DynamicOperatingEnvelopesProgram(Program):
    # polymorphic_identity is used by the orm to identify the program type
    __mapper_args__: dict = {"polymorphic_identity": ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES}

    def _check_control_options(self, opts: list[ControlOptionsEnum]):
        if len(opts) > 1:
            raise ProgramSaveViolation("Only one control option can be set for DOE programs")
        if len(opts) > 0 and opts[0] not in ControlOptionsEnum.get_doe_control_options():
            raise ProgramSaveViolation(f"Control option {opts[0]} is not valid for DOE programs")

    def _check_control_type(self, opts: list[ControlOptionsEnum]):
        requires_control_type = opts[0] == ControlOptionsEnum.CSIP_AUS
        if not requires_control_type and self.control_type:
            raise ProgramSaveViolation(
                "Control type can only be set for DOE programs with control option CSIP_AUS"
            )
        elif requires_control_type and not self.control_type:
            raise ProgramSaveViolation("Control option CSIP_AUS requires a control type")

    def _validate_control_options_and_type(self):
        """Control Options must be one of the following:
        - CSIP_AUS
        - CSIP
        If the type is CSIP_AUS, then the control type must also be set
        """
        if not self.control_options and not self.control_type:
            return
        self._check_control_options(self.control_options or [])
        self._check_control_type(self.control_options or [])

    def _update_program_specific_fields(self, data: CreateUpdateProgram):
        if data.control_options is not None:
            self.control_options = data.control_options
        doe_fields = data.dynamic_operating_envelope_fields
        if doe_fields:
            self.limit_type = doe_fields.limit_type or self.limit_type
            self.calculation_frequency = (
                doe_fields.calculation_frequency or self.calculation_frequency
            )
            self.schedule_time_horizon_timeperiod = (
                doe_fields.schedule_time_horizon_timeperiod or self.schedule_time_horizon_timeperiod
            )
            if doe_fields.schedule_time_horizon_number is not None:
                self.schedule_time_horizon_number = doe_fields.schedule_time_horizon_number
            if doe_fields.schedule_timestep_mins is not None:
                self.schedule_timestep_mins = doe_fields.schedule_timestep_mins
            if doe_fields.control_type is not None:
                self.control_type = doe_fields.control_type
        self._validate_control_options_and_type()


class DemandManagementProgram(Program):
    # polymorphic_identity is used by the orm to identify the program type
    __mapper_args__: dict = {"polymorphic_identity": ProgramTypeEnum.DEMAND_MANAGEMENT}

    def _update_program_specific_fields(self, data: CreateUpdateProgram):
        self.dispatch_constraints = data.dispatch_constraints or self.dispatch_constraints
        self.demand_management_constraints = (
            data.demand_management_constraints or self.demand_management_constraints
        )


@dataclass
class GenericFields(DataClassJsonMixin):
    name: Optional[str] = None
    program_type: Optional[ProgramTypeEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    program_priority: Optional[ProgramPriority] = None
    availability_type: Optional[AvailabilityType] = None
    check_der_eligibility: Optional[bool] = None
    define_contractual_target_capacity: Optional[bool] = None
    status: Optional[ProgramStatus] = None
    notification_type: Optional[NotificationType] = None


@dataclass
class CreateUpdateProgram(DataClassJsonMixin):
    general_fields: GenericFields
    dispatch_constraints: Optional[Constraints] = None
    demand_management_constraints: Optional[DemandManagementConstraints] = None
    resource_eligibility_criteria: Optional[ResourceEligibilityCriteria] = None
    avail_operating_months: Optional[dict] = None
    dispatch_max_opt_outs: Optional[list[dict]] = None
    dispatch_notifications: Optional[list[dict]] = None
    avail_service_windows: Optional[list[dict]] = None
    dynamic_operating_envelope_fields: Optional[DynamicOperatingEnvelopeFields] = None
    control_options: Optional[list[ControlOptionsEnum]] = None
    dispatch_type: Optional[DispatchTypeEnum] = None
    track_event: Optional[bool] = None


@dataclass
class DynamicOperatingEnvelopeFields(DataClassJsonMixin):
    limit_type: Optional[DOELimitType] = None
    calculation_frequency: Optional[DOECalculationFrequency] = None
    control_type: Optional[list[DOEControlType]] = None
    schedule_time_horizon_timeperiod: Optional[ScheduleTimeperiod] = None
    schedule_time_horizon_number: Optional[int] = None
    schedule_timestep_mins: Optional[int] = None


class ProgramNameDuplicate(Error):
    pass


class InvalidProgramStartEndTimes(Error):
    pass


class ProgramSaveViolation(Error):
    pass


class InvalidProgramStatus(Error):
    pass


# ================ TYPING DEFINITIONS ================ #


class HolidayCalendarEventsDict(TypedDict):
    startDate: str
    endDate: str
    name: str
    category: Optional[str]
    substitutionDate: Optional[str]


class HolidayCalendarInfoDict(TypedDict):
    mrid: str
    timezone: str
    year: int
    events: list[HolidayCalendarEventsDict]
