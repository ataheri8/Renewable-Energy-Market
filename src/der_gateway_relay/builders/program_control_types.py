import abc
from typing import Any

from lxml import etree as ET

from shared.enums import ControlOptionsEnum, DOEControlType, ProgramTypeEnum
from shared.tools.utils import convert_from_snake_to_camel_case
from shared.validators.der_gateway_data import DerGatewayProgram

SUPPORTED_CONTROL_TYPE_LIST = "supportedControlTypeList"
SUPPORTED_CONTROL_TYPE = "supportedControlType"
SUPPORTED_DOE_CONTROL_TYPE = "supportedDoeControlType"
SUPPORTED_DOE_CONTROL_TYPE_LIST = "supportedDoeControlTypeList"

OP_MOD_MAX_LIM_W = "opModMaxLimW"
OP_MOD_EXP_LIM_W = "opModExpLimW"
OP_MOD_IMP_LIM_W = "opModImpLimW"
OP_MOD_GEN_LIM_W = "opModGenLimW"
OP_MOD_LOAD_LIM_W = "opModLoadLimW"
OP_MOD_FIXED_W = "opModFixedW"


class ControlTypeStrategy(abc.ABC):
    """Base class for control type strategies.

    Given a DERGatewayProgram object, build the XML control type list for the program.
    """

    def _build_xml_list(
        self,
        control_type_text: list[str],
        control_type_wrapper: str,
        control_type_list_wrapper: str,
    ) -> Any:
        supported_control_type_list = ET.Element(control_type_list_wrapper)
        for control_type in control_type_text:
            supported_control_type = ET.SubElement(
                supported_control_type_list, control_type_wrapper
            )
            supported_control_type.text = control_type
        if len(supported_control_type_list) == 0:
            return None
        return supported_control_type_list

    @abc.abstractmethod
    def build_xml(self, obj: DerGatewayProgram) -> list[Any]:
        pass

    @classmethod
    def build_control_type_list(cls, obj: DerGatewayProgram) -> list[Any]:
        """Build the control type list for the program.
        Returns a list of LXML objects, which are not typed
        """
        if str(obj.program.program_type) == str(ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES):
            return DynamicOperatingEnvelopeControlTypePolicy().build_xml(obj)
        elif str(obj.program.program_type) == str(ProgramTypeEnum.DEMAND_MANAGEMENT):
            return DemandManagementControlTypePolicy().build_xml(obj)
        else:
            return GenericControlTypePolicy().build_xml(obj)


class GenericControlTypePolicy(ControlTypeStrategy):
    def build_xml(self, obj: DerGatewayProgram) -> list[Any]:
        control_type_text = []
        control_type_list_wrapper = SUPPORTED_CONTROL_TYPE_LIST
        control_type_wrapper = SUPPORTED_CONTROL_TYPE

        control_type_text += [
            convert_from_snake_to_camel_case(o.name) for o in obj.program.control_options or []
        ]
        return [
            self._build_xml_list(control_type_text, control_type_wrapper, control_type_list_wrapper)
        ]


class DynamicOperatingEnvelopeControlTypePolicy(ControlTypeStrategy):
    DOE_MAPPINGS = {
        DOEControlType.CONNECTION_POINT_EXPORT_LIMIT: OP_MOD_EXP_LIM_W,
        DOEControlType.CONNECTION_POINT_IMPORT_LIMIT: OP_MOD_IMP_LIM_W,
        DOEControlType.DER_EXPORT_LIMIT: OP_MOD_GEN_LIM_W,
        DOEControlType.DER_IMPORT_LIMIT: OP_MOD_LOAD_LIM_W,
    }

    def _build_doe_default_control_types(self) -> Any:
        """Builds the default control types for DOE programs.

        This is required because the current version of DER Gateway (v2.3.0) does not support
        supportedDoeControlTypes without a supportedControlType.

        This may change in the future
        """
        DEFAULT_FOR_DOE_WITH_SUPPORTED_DOE_TYPE = OP_MOD_FIXED_W
        return self._build_xml_list(
            [DEFAULT_FOR_DOE_WITH_SUPPORTED_DOE_TYPE],
            SUPPORTED_CONTROL_TYPE,
            SUPPORTED_CONTROL_TYPE_LIST,
        )

    def build_xml(self, obj: DerGatewayProgram) -> list[Any]:
        control_type_text = []
        control_type_list_wrapper = SUPPORTED_CONTROL_TYPE_LIST
        control_type_wrapper = SUPPORTED_CONTROL_TYPE
        ctrl_options = obj.program.control_options or []

        xml_list: list[Any] = []

        if ControlOptionsEnum.CSIP_AUS in ctrl_options:
            control_type_list_wrapper = SUPPORTED_DOE_CONTROL_TYPE_LIST
            control_type_wrapper = SUPPORTED_DOE_CONTROL_TYPE
            control_type_text += [
                self.DOE_MAPPINGS.get(o, "") for o in obj.program.control_type or []
            ]
            default_doe_control_types = self._build_doe_default_control_types()
            doe_control_types = self._build_xml_list(
                control_type_text, control_type_wrapper, control_type_list_wrapper
            )
            xml_list.append(default_doe_control_types)
            xml_list.append(doe_control_types)
        else:
            control_type_text.append(OP_MOD_MAX_LIM_W)
            xml_list.append(
                self._build_xml_list(
                    control_type_text, control_type_wrapper, control_type_list_wrapper
                )
            )
        return xml_list


class DemandManagementControlTypePolicy(ControlTypeStrategy):
    def build_xml(self, _: DerGatewayProgram) -> list[Any]:
        control_type_text = []
        control_type_list_wrapper = SUPPORTED_CONTROL_TYPE_LIST
        control_type_wrapper = SUPPORTED_CONTROL_TYPE

        control_type_text.append(OP_MOD_FIXED_W)

        return [
            self._build_xml_list(control_type_text, control_type_wrapper, control_type_list_wrapper)
        ]
