import abc
import calendar
import datetime
from collections import OrderedDict
from dataclasses import asdict, dataclass
from itertools import groupby
from operator import itemgetter
from typing import Any, Optional

import pendulum
from dataclasses_json import DataClassJsonMixin
from lxml import etree as ET

from shared.system import loggingsys
from shared.utils import recursive_getattr
from shared.validators.der_gateway_data import (
    DerGatewayProgram,
    _AvailServiceWindows,
    _HolidayCalendars,
    _MinMax,
)

# Service windows constants
MINIMUM_START_HOUR = 0
MAXIMUM_START_HOUR = 23
MINIMUM_END_HOUR = 1
MAXIMUM_END_HOUR = 24

# Program constraint element constants
PROGRAM_CONSTRAINT = "programConstraint"

# National holiday constants
NATIONAL_HOLIDAY = "National Holiday"

logger = loggingsys.get_logger(__name__)


class BuildConstraintXML(abc.ABC):
    """
    Class made to build program constraints with limit
    """

    CONSTRAINT_TYPE = ""

    @classmethod
    @abc.abstractmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        pass

    def _get_limit_constraint(self, limit: int | float | None) -> Any:
        program_constraint = ET.Element(PROGRAM_CONSTRAINT)
        if not limit or limit < 1:
            return None
        limit_constraint = ProgramLimitConstraint(self.CONSTRAINT_TYPE, str(int(limit)))
        self._create_sub_element(program_constraint, limit_constraint.to_dict())
        return program_constraint

    def _get_nested_attribute(self, obj: DerGatewayProgram, attribute: str) -> Any:
        """
        Get nested attribute from object
        """
        try:
            return recursive_getattr(obj, attribute)
        except AttributeError:
            return None

    def _get_cumulative_event_duration(
        self, obj: DerGatewayProgram, timeperiod_str: str
    ) -> Optional[int]:
        """Gets data for all constraints that use dispatch_constraints.cumulative_event_duration"""
        prop: Optional[dict[str, _MinMax]] = self._get_nested_attribute(
            obj,
            "program.dispatch_constraints.cumulative_event_duration",
        )
        if not prop or not prop.get(timeperiod_str):
            return None
        return self._get_limit_constraint(prop[timeperiod_str].max)

    def _get_max_number_of_events_limit(
        self, obj: DerGatewayProgram, timeperiod_str: str
    ) -> Optional[int]:
        """
        Gets data for all constraints that use
        dispatch_constraints.max_number_of_events_per_timeperiod
        """
        builder = self
        prop: Optional[dict[str, int]] = builder._get_nested_attribute(
            obj,
            "program.dispatch_constraints.max_number_of_events_per_timeperiod",
        )
        if not prop or not prop.get(timeperiod_str):
            return None
        return self._get_limit_constraint(prop[timeperiod_str])

    def _create_sub_element(self, root: Any, sub_element_dict: dict):
        """
        Appending XML sub elements to the given root element
        """
        for key, value in sub_element_dict.items():
            new_element = ET.SubElement(root, key)
            new_element.text = value

    def _construct_operational_list(self, obj: dict, dict_map: OrderedDict) -> list[dict[str, str]]:
        """
        Pass in mapped dictionary by ordered string and interger allong with object to map
        output ranges of consecutive items with a start and end position
        """
        day_list = []

        for key, value in obj.items():
            if str(value).strip().lower() == "true":
                day_list.append(dict_map[key])

        if day_list is None:
            return []

        operational_days_list = []
        key_list = list(dict_map.keys())
        value_list = list(dict_map.values())
        for _, g in groupby(enumerate(day_list), lambda ix: ix[0] - ix[1]):
            consecutive_days = list(map(itemgetter(1), g))
            start_position = value_list.index(consecutive_days[0])
            end_position = value_list.index(consecutive_days[-1])

            month_range = {"start": key_list[start_position], "end": key_list[end_position]}
            operational_days_list.append(month_range)

        return operational_days_list


@dataclass
class ProgramTimeConstraint(DataClassJsonMixin):
    programConstraintType: str
    programConstraintStart: str
    programConstraintEnd: str


@dataclass
class ProgramLimitConstraint(DataClassJsonMixin):
    programConstraintType: str
    programConstraintLimit: str


@dataclass
class ProgramTypeOnlyConstraint(DataClassJsonMixin):
    programConstraintType: str


class BuildProgramConstraintTypeOne(BuildConstraintXML):
    """
    Builds program constraint in xml format
    It includes constraint type, start hour and end hour
    Constraint type one focuses on the start and end hours in a given day between 0 and 23
    """

    CONSTRAINT_TYPE = "1"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        builder = cls()
        xml_list: list[Any] = []
        for service_window in obj.program.avail_service_windows or []:
            program_constraint_dict = builder.construct_service_window_constraint(service_window)
            if program_constraint_dict is not None:
                program_constraint = ET.Element(PROGRAM_CONSTRAINT)
                builder._create_sub_element(program_constraint, program_constraint_dict)
                xml_list.append(program_constraint)
        return xml_list

    def construct_service_window_constraint(self, obj: _AvailServiceWindows) -> Any:
        """
        Builds the applicable service window constraint from passed in dictionary
        """
        if not (MINIMUM_START_HOUR <= obj.start_hour <= MAXIMUM_START_HOUR):
            return None
        if not (MINIMUM_END_HOUR <= obj.end_hour <= MAXIMUM_END_HOUR):
            return None
        if obj.start_hour >= obj.end_hour:
            return None

        type_one_constraint = ProgramTimeConstraint(
            self.CONSTRAINT_TYPE, str(obj.start_hour), str(obj.end_hour)
        )
        return type_one_constraint.to_dict()


class BuildProgramConstraintTypeTwo(BuildConstraintXML):
    """
    Builds program constraint in xml format
    It includes constraint type, start hour and end hour
    Constraint type two focuses on the start and end days in a given day between the week
    """

    CONSTRAINT_TYPE = "2"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        builder = cls()
        day_to_range_map = OrderedDict(
            [
                ("mon", 1),
                ("tue", 2),
                ("wed", 3),
                ("thu", 4),
                ("fri", 5),
                ("sat", 6),
                ("sun", 7),
            ]
        )
        xml_list: list[Any] = []
        for delivery_days in obj.program.avail_service_windows or []:
            delivery_days_list = builder._construct_operational_list(
                asdict(delivery_days), day_to_range_map
            )

            for deliver_day_constraint in delivery_days_list:
                program_constraint = ET.Element(PROGRAM_CONSTRAINT)
                type_two_constraint = ProgramTimeConstraint(
                    builder.CONSTRAINT_TYPE,
                    deliver_day_constraint["start"],
                    deliver_day_constraint["end"],
                )
                builder._create_sub_element(program_constraint, type_two_constraint.to_dict())
                xml_list.append(program_constraint)
        return xml_list


class BuildProgramConstraintTypeThree(BuildConstraintXML):
    """
    Builds program constraint in xml format
    It includes constraint type, start and end
    Constraint type two focuses on the start and end days in a given day between the week
    """

    CONSTRAINT_TYPE = "3"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        builder = cls()
        holiday_calendars: list[_HolidayCalendars] = builder._get_nested_attribute(
            obj, "program.holiday_exclusions.calendars"
        )

        xml_list: list[Any] = []
        for holiday_calendar in holiday_calendars or []:
            for event in holiday_calendar.events:
                try:
                    if event.category == NATIONAL_HOLIDAY:
                        type_three_constraint = ProgramTypeOnlyConstraint(builder.CONSTRAINT_TYPE)
                        program_constraint = ET.Element(PROGRAM_CONSTRAINT)
                        builder._create_sub_element(
                            program_constraint, type_three_constraint.to_dict()
                        )
                        xml_list.append(program_constraint)
                        break
                except KeyError:
                    pass
        return xml_list


class BuildProgramConstraintTypeFour(BuildConstraintXML):
    """
    Builds program constraint in xml format
    It includes constraint type, start and end
    Constraint type two focuses on the start and end days in a given day between the week
    """

    CONSTRAINT_TYPE = "4"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        xml_list: list[Any] = []
        if not obj.program.avail_service_windows or not obj.program.avail_operating_months:
            return xml_list
        builder = cls()
        month_mapping = OrderedDict(
            [
                ("jan", 1),
                ("feb", 2),
                ("mar", 3),
                ("apr", 4),
                ("may", 5),
                ("jun", 6),
                ("jul", 7),
                ("aug", 8),
                ("sep", 9),
                ("oct", 10),
                ("nov", 11),
                ("dec", 12),
            ]
        )

        op_months = builder._construct_operational_list(
            asdict(obj.program.avail_operating_months), month_mapping
        )

        program_start_date = obj.program.start_date
        start_date = pendulum.parse(program_start_date)

        for op_month in op_months:
            end_day = op_month["end"]

            month_integer = datetime.datetime.strptime(end_day, "%b").month
            month_end = calendar.monthrange(start_date.year, month_integer)  # type: ignore
            ending_month = str(month_end[1])

            type_four_constraint = ProgramTimeConstraint(
                builder.CONSTRAINT_TYPE, op_month["start"] + "1", op_month["end"] + ending_month
            )
            program_constraint = ET.Element(PROGRAM_CONSTRAINT)
            builder._create_sub_element(program_constraint, type_four_constraint.to_dict())
            xml_list.append(program_constraint)
        return xml_list


class BuildProgramConstraintTypeFive(BuildConstraintXML):
    CONSTRAINT_TYPE = "5"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        builder = cls()
        attribute: Optional[int] = builder._get_nested_attribute(
            obj, "program.dispatch_constraints.event_duration_constraint.min"
        )
        if not attribute:
            return []
        return [cls()._get_limit_constraint(attribute)]


class BuildProgramConstraintTypeSix(BuildConstraintXML):
    CONSTRAINT_TYPE = "6"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        builder = cls()
        attribute: Optional[int] = builder._get_nested_attribute(
            obj, "program.dispatch_constraints.event_duration_constraint.max"
        )
        if not attribute:
            return []
        return [cls()._get_limit_constraint(attribute)]


class BuildProgramConstraintTypeSeven(BuildConstraintXML):
    CONSTRAINT_TYPE = "7"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        return [cls()._get_cumulative_event_duration(obj, "DAY")]


class BuildProgramConstraintTypeEight(BuildConstraintXML):
    CONSTRAINT_TYPE = "8"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        return [cls()._get_cumulative_event_duration(obj, "MONTH")]


class BuildProgramConstraintTypeNine(BuildConstraintXML):
    CONSTRAINT_TYPE = "9"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        return [cls()._get_cumulative_event_duration(obj, "YEAR")]


class BuildProgramConstraintTypeTen(BuildConstraintXML):
    CONSTRAINT_TYPE = "10"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        return [cls()._get_max_number_of_events_limit(obj, "DAY")]


class BuildProgramConstraintTypeEleven(BuildConstraintXML):
    CONSTRAINT_TYPE = "11"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        return [cls()._get_max_number_of_events_limit(obj, "MONTH")]


class BuildProgramConstraintTypeTwelve(BuildConstraintXML):
    CONSTRAINT_TYPE = "12"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        return [cls()._get_max_number_of_events_limit(obj, "YEAR")]


class BuildProgramConstraintTypeThirteen(BuildConstraintXML):
    CONSTRAINT_TYPE = "13"

    @classmethod
    def build_constraint(cls, obj: DerGatewayProgram) -> list[Any]:
        builder = cls()
        attribute: Optional[int] = builder._get_nested_attribute(
            obj, "program.demand_management_constraints.max_total_energy_per_timeperiod"
        )
        if not attribute:
            return []
        return [cls()._get_limit_constraint(attribute)]
