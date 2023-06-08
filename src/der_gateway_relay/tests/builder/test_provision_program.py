from der_gateway_relay.builders.provision_program import ProvisionProgramBuilder
from der_gateway_relay.tests.builder.mixins import AssertXMLEqualsMixin


def _create_program_data(name: str, id: int):
    return (
        """<Program>
    <programId>"""
        + str(id)
        + """</programId>
    <programName>"""
        + name
        + """</programName>
    <programType>DEMAND_MANAGEMENT</programType>
    <programStartDate>2021-01-01</programStartDate>
    <programEndDate>2021-12-31</programEndDate>
    <programDispatchPriority>1</programDispatchPriority>
    <vppContract>true</vppContract>
    <supportedControlTypeList>
      <supportedControlType>opModFixedW</supportedControlType>
    </supportedControlTypeList>
  </Program>"""
    )


def create_program_xml_str(number_of_programs: int = 1):
    """Create test program XML string with the given number of programs"""
    program_str = ""
    for i in range(number_of_programs):
        index = i + 1
        program_str += _create_program_data(f"Test Program {index}", index)
    return (
        """
<ProgramList action="add" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="com:ge:ieee2030:registration:rest:ext:dto">
    """  # noqa: E501
        + program_str
        + "</ProgramList>"
    )


class TestProvisionProgram(AssertXMLEqualsMixin):
    def test_create_provision_program(self):
        expected_xml_str = """<ProgramDataList all="0" results="0" xmlns="com:ge:ieee2030:registration:rest:dto">
  <ProgramData>
    <programId>1</programId>
    <programName>Test Program 1</programName>
    <programType>DEMAND_MANAGEMENT</programType>
    <programStartDate>2021-01-01</programStartDate>
    <programEndDate>2021-12-31</programEndDate>
    <programDispatchPriority>1</programDispatchPriority>
    <vppContract>true</vppContract>
    <supportedControlTypeList>
      <supportedControlType>opModFixedW</supportedControlType>
    </supportedControlTypeList>
    <programLifeCycleStatus>registered</programLifeCycleStatus>
  </ProgramData>
</ProgramDataList>"""  # noqa: E501
        program_xml_str = create_program_xml_str()
        provision_program_xml_str = ProvisionProgramBuilder.build(program_xml_str)
        self.assert_xml_str_equals(provision_program_xml_str, expected_xml_str)

    def test_create_provision_program_with_multiple_programs(self):
        expected_xml_str = """
<ProgramDataList all="0" results="0" xmlns="com:ge:ieee2030:registration:rest:dto">
    <ProgramData>
        <programId>1</programId>
        <programName>Test Program 1</programName>
        <programType>DEMAND_MANAGEMENT</programType>
        <programStartDate>2021-01-01</programStartDate>
        <programEndDate>2021-12-31</programEndDate>
        <programDispatchPriority>1</programDispatchPriority>
        <vppContract>true</vppContract>
        <supportedControlTypeList>
            <supportedControlType>opModFixedW</supportedControlType>
        </supportedControlTypeList>
        <programLifeCycleStatus>registered</programLifeCycleStatus>
    </ProgramData>
    <ProgramData>
        <programId>2</programId>
        <programName>Test Program 2</programName>
        <programType>DEMAND_MANAGEMENT</programType>
        <programStartDate>2021-01-01</programStartDate>
        <programEndDate>2021-12-31</programEndDate>
        <programDispatchPriority>1</programDispatchPriority>
        <vppContract>true</vppContract>
        <supportedControlTypeList>
            <supportedControlType>opModFixedW</supportedControlType>
        </supportedControlTypeList>
        <programLifeCycleStatus>registered</programLifeCycleStatus>
    </ProgramData>
</ProgramDataList>"""
        program_xml_str = create_program_xml_str(2)
        provision_program_xml_str = ProvisionProgramBuilder.build(program_xml_str)
        self.assert_xml_str_equals(provision_program_xml_str, expected_xml_str)
