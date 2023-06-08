from __future__ import annotations

import abc
from dataclasses import dataclass
from enum import Enum
from typing import Any, Type

import pendulum
from dataclasses_json import DataClassJsonMixin
from lxml import etree as ET

from der_gateway_relay.builders.program_constraints import (
    BuildConstraintXML,
    BuildProgramConstraintTypeEight,
    BuildProgramConstraintTypeEleven,
    BuildProgramConstraintTypeFive,
    BuildProgramConstraintTypeFour,
    BuildProgramConstraintTypeNine,
    BuildProgramConstraintTypeOne,
    BuildProgramConstraintTypeSeven,
    BuildProgramConstraintTypeSix,
    BuildProgramConstraintTypeTen,
    BuildProgramConstraintTypeThirteen,
    BuildProgramConstraintTypeThree,
    BuildProgramConstraintTypeTwelve,
    BuildProgramConstraintTypeTwo,
)
from der_gateway_relay.builders.program_control_types import ControlTypeStrategy
from shared.enums import ProgramPriority, ProgramTypeEnum
from shared.validators.der_gateway_data import DerGatewayProgram


class BuildBaseXML(abc.ABC):
    """
    Takes data from PM in form of Kafka messages
    Outputs XML for Program, ProgramEnrollment,
    along with associated constraints excluding limit types
    """

    @classmethod
    @abc.abstractmethod
    def build(cls, obj: list[DerGatewayProgram]) -> str:
        pass

    def _create_sub_element(self, root: Any, sub_element_dict: dict):
        """
        Appending XML sub elements to the given root element
        """
        for key, value in sub_element_dict.items():
            new_element = ET.SubElement(root, key)
            if isinstance(value, Enum):
                new_element.text = value.name
            else:
                new_element.text = value

    def _convert_to_time_type(self, time_str: str):
        return pendulum.parse(time_str)


@dataclass
class Enrollment(DataClassJsonMixin):
    enrollmentId: str
    derMrid: str
    enrollmentStartDate: str
    enrollmentEndDate: str
    programId: str


class BuildEnrollmentXML(BuildBaseXML):
    @classmethod
    def build(cls, obj: list[DerGatewayProgram], action: str = "add") -> str:
        builder = cls()

        program_enrollment_list = ET.Element(
            "ProgramEnrollmentList",
            action=action,
            xmlns="com:ge:ieee2030:registration:rest:ext:dto",
            nsmap={
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            },
        )

        for enrollment in obj:
            child_element = builder._convert_json_to_program_enrollment_xml(enrollment)
            program_enrollment_list.append(child_element)
        return ET.tostring(program_enrollment_list).decode("utf-8")

    def _convert_json_to_program_enrollment_xml(self, obj: DerGatewayProgram) -> Any:
        enrollment_dataclass = Enrollment(
            str(obj.contract.id),
            obj.enrollment.der_id,
            self._convert_to_time_type(obj.program.start_date).strftime("%Y-%m-%dT%H:%M:%S"),
            self._convert_to_time_type(obj.program.end_date).strftime("%Y-%m-%dT%H:%M:%S"),
            str(obj.contract.id),
        )
        program_enrollment = ET.Element("programEnrollment")
        self._create_sub_element(program_enrollment, enrollment_dataclass.to_dict())
        return program_enrollment


@dataclass
class Program(DataClassJsonMixin):
    programId: str
    programName: str
    programType: str
    programStartDate: str
    programEndDate: str
    programDispatchPriority: str
    vppContract: str


class BuildProgramXML(BuildBaseXML):
    @classmethod
    def build(cls, obj: list[DerGatewayProgram], action: str = "add") -> str:
        builder = cls()

        program_list = ET.Element(
            "ProgramList",
            action=action,
            xmlns="com:ge:ieee2030:registration:rest:ext:dto",
            nsmap={
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            },
        )

        for program in obj:
            child_element = builder._convert_json_to_program_xml(program)
            program_constraint_list = builder._build_constraints(program)
            if program_constraint_list is not None:
                child_element.append(program_constraint_list)
            program_list.append(child_element)
        return ET.tostring(program_list).decode("utf-8")

    def _get_priority_for_der_gateway(self, obj: DerGatewayProgram) -> str:
        """Map the priority to the priority used by the DER Gateway."""
        if not obj.program.program_priority:
            return "99"  # Default to 99 for DER Gateway
        priority_map = {
            ProgramPriority.P0: "1",
            ProgramPriority.P1: "2",
            ProgramPriority.P2: "3",
            ProgramPriority.P3: "4",
            ProgramPriority.P4: "5",
            ProgramPriority.P5: "6",
        }
        return priority_map.get(obj.program.program_priority, "1")  # Default to P0

    def _convert_json_to_program_xml(self, obj: DerGatewayProgram) -> Any:
        vpp_contract = "false"
        if obj.program.program_type.value == ProgramTypeEnum.DEMAND_MANAGEMENT.value:
            vpp_contract = "true"

        program_dataclass = Program(
            str(obj.contract.id),
            obj.program.name,
            obj.program.program_type.value,
            self._convert_to_time_type(obj.program.start_date).to_date_string(),
            self._convert_to_time_type(obj.program.end_date).to_date_string(),
            self._get_priority_for_der_gateway(obj),
            vpp_contract,
        )

        program = ET.Element("Program")

        self._create_sub_element(program, program_dataclass.to_dict())
        supported_control_type_list = ControlTypeStrategy.build_control_type_list(obj)
        for element in supported_control_type_list:
            program.append(element)
        return program

    def _build_constraints(self, obj: DerGatewayProgram) -> Any:
        constraint_list = ET.Element("programConstraintList")
        constraints: list[Type[BuildConstraintXML]] = [
            BuildProgramConstraintTypeOne,
            BuildProgramConstraintTypeTwo,
            BuildProgramConstraintTypeThree,
            BuildProgramConstraintTypeFour,
            BuildProgramConstraintTypeFive,
            BuildProgramConstraintTypeSix,
            BuildProgramConstraintTypeSeven,
            BuildProgramConstraintTypeEight,
            BuildProgramConstraintTypeNine,
            BuildProgramConstraintTypeTen,
            BuildProgramConstraintTypeEleven,
            BuildProgramConstraintTypeTwelve,
            BuildProgramConstraintTypeThirteen,
        ]
        for c in constraints:
            xml_list = c.build_constraint(obj)
            for val in xml_list:
                if val is not None:
                    constraint_list.append(val)

        if len(constraint_list) == 0:
            return None
        return constraint_list
