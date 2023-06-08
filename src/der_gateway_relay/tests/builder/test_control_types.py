from der_gateway_relay.builders.program_control_types import ControlTypeStrategy
from der_gateway_relay.tests.builder.mixins import AssertXMLEqualsMixin
from shared.enums import ControlOptionsEnum, DOEControlType, ProgramTypeEnum
from shared.validators.der_gateway_data import DerGatewayProgram


class TestControlTypeStrategies(AssertXMLEqualsMixin):
    def test_generic_control_type(self, single_payload: DerGatewayProgram):
        expected = """
<supportedControlTypeList>
  <supportedControlType>opModFixedW</supportedControlType>
  <supportedControlType>opModVoltVar</supportedControlType>
</supportedControlTypeList>
"""
        single_payload.program.program_type = ProgramTypeEnum.GENERIC
        single_payload.program.control_options = [
            ControlOptionsEnum.OP_MOD_FIXED_W,
            ControlOptionsEnum.OP_MOD_VOLT_VAR,
        ]
        got = ControlTypeStrategy.build_control_type_list(single_payload)
        self.assert_xml_equals(expected, got[0])

    def test_demand_management_control_type(self, single_payload: DerGatewayProgram):
        expected = """
<supportedControlTypeList>
  <supportedControlType>opModFixedW</supportedControlType>
</supportedControlTypeList>
"""
        single_payload.program.program_type = ProgramTypeEnum.DEMAND_MANAGEMENT
        single_payload.program.control_options = []
        got = ControlTypeStrategy.build_control_type_list(single_payload)
        self.assert_xml_equals(expected, got[0])

    def test_dynamic_operating_envelope_control_type_doe_control_type(
        self, single_payload: DerGatewayProgram
    ):
        expected_1 = """
<supportedControlTypeList>
  <supportedControlType>opModFixedW</supportedControlType>
</supportedControlTypeList>
        """
        expected_2 = """
<supportedDoeControlTypeList>
  <supportedDoeControlType>opModExpLimW</supportedDoeControlType>
  <supportedDoeControlType>opModImpLimW</supportedDoeControlType>
  <supportedDoeControlType>opModGenLimW</supportedDoeControlType>
  <supportedDoeControlType>opModLoadLimW</supportedDoeControlType>
</supportedDoeControlTypeList>
"""
        single_payload.program.program_type = ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES
        single_payload.program.control_options = [ControlOptionsEnum.CSIP_AUS]
        single_payload.program.control_type = [
            DOEControlType.CONNECTION_POINT_EXPORT_LIMIT,
            DOEControlType.CONNECTION_POINT_IMPORT_LIMIT,
            DOEControlType.DER_EXPORT_LIMIT,
            DOEControlType.DER_IMPORT_LIMIT,
        ]
        got = ControlTypeStrategy.build_control_type_list(single_payload)
        self.assert_xml_equals(expected_1, got[0])
        self.assert_xml_equals(expected_2, got[1])

    def test_dynamic_operating_envelope_control_type_normal_control_type(
        self, single_payload: DerGatewayProgram
    ):
        expected = """
<supportedControlTypeList>
  <supportedControlType>opModMaxLimW</supportedControlType>
</supportedControlTypeList>
"""
        single_payload.program.program_type = ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES
        single_payload.program.control_options = [ControlOptionsEnum.CSIP]
        single_payload.program.control_type = []
        got = ControlTypeStrategy.build_control_type_list(single_payload)
        self.assert_xml_equals(expected, got[0])
