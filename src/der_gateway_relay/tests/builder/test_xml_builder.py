from der_gateway_relay.builders.program import BuildEnrollmentXML, BuildProgramXML
from der_gateway_relay.tests.builder.mixins import AssertXMLEqualsMixin
from shared.enums import DOEControlType, ProgramTypeEnum


class TestBuildEnrollmentXML(AssertXMLEqualsMixin):
    def test_create_enrollment_xml(self, single_payload):
        xml_str = """
<ProgramEnrollmentList action="add" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="com:ge:ieee2030:registration:rest:ext:dto">
  <programEnrollment>
    <enrollmentId>1</enrollmentId>
    <derMrid>der_id</derMrid>
    <enrollmentStartDate>2021-01-01T00:00:00</enrollmentStartDate>
    <enrollmentEndDate>2021-12-31T00:00:00</enrollmentEndDate>
    <programId>1</programId>
  </programEnrollment>
  <programEnrollment>
    <enrollmentId>1</enrollmentId>
    <derMrid>der_id</derMrid>
    <enrollmentStartDate>2021-01-01T00:00:00</enrollmentStartDate>
    <enrollmentEndDate>2021-12-31T00:00:00</enrollmentEndDate>
    <programId>1</programId>
  </programEnrollment>
</ProgramEnrollmentList>
        """  # noqa: E501
        enrollment_XML = BuildEnrollmentXML.build([single_payload, single_payload])
        self.assert_xml_str_equals(xml_str, enrollment_XML)


class TestBuildProgramXML(AssertXMLEqualsMixin):
    def test_create_program_xml(self, single_payload):
        xml_str = """
<ProgramList action="add" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="com:ge:ieee2030:registration:rest:ext:dto">
  <Program>
    <programId>1</programId>
    <programName>Test Program</programName>
    <programType>DEMAND_MANAGEMENT</programType>
    <programStartDate>2021-01-01</programStartDate>
    <programEndDate>2021-12-31</programEndDate>
    <programDispatchPriority>1</programDispatchPriority>
    <vppContract>true</vppContract>
    <supportedControlTypeList>
      <supportedControlType>opModFixedW</supportedControlType>
    </supportedControlTypeList>
    <programConstraintList>
      <programConstraint>
        <programConstraintType>1</programConstraintType>
        <programConstraintStart>0</programConstraintStart>
        <programConstraintEnd>23</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>2</programConstraintType>
        <programConstraintStart>mon</programConstraintStart>
        <programConstraintEnd>sun</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>3</programConstraintType>
      </programConstraint>
      <programConstraint>
        <programConstraintType>4</programConstraintType>
        <programConstraintStart>jan1</programConstraintStart>
        <programConstraintEnd>dec31</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>5</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>6</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>7</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>8</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>9</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>10</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>11</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>12</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>13</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
    </programConstraintList>
  </Program>
  <Program>
    <programId>1</programId>
    <programName>Test Program</programName>
    <programType>DEMAND_MANAGEMENT</programType>
    <programStartDate>2021-01-01</programStartDate>
    <programEndDate>2021-12-31</programEndDate>
    <programDispatchPriority>1</programDispatchPriority>
    <vppContract>true</vppContract>
    <supportedControlTypeList>
      <supportedControlType>opModFixedW</supportedControlType>
    </supportedControlTypeList>
    <programConstraintList>
      <programConstraint>
        <programConstraintType>1</programConstraintType>
        <programConstraintStart>0</programConstraintStart>
        <programConstraintEnd>23</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>2</programConstraintType>
        <programConstraintStart>mon</programConstraintStart>
        <programConstraintEnd>sun</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>3</programConstraintType>
      </programConstraint>
      <programConstraint>
        <programConstraintType>4</programConstraintType>
        <programConstraintStart>jan1</programConstraintStart>
        <programConstraintEnd>dec31</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>5</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>6</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>7</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>8</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>9</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>10</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>11</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>12</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>13</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
    </programConstraintList>
  </Program>
</ProgramList>
        """  # noqa: E501
        program_XML = BuildProgramXML.build([single_payload, single_payload])
        self.assert_xml_str_equals(xml_str, program_XML)

    def test_create_DYNAMIC_OPERATING_ENVELOPES_program_xml(self, single_payload):
        xml_str = """
<ProgramList action="add" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="com:ge:ieee2030:registration:rest:ext:dto">
  <Program>
    <programId>1</programId>
    <programName>Test Program</programName>
    <programType>DYNAMIC_OPERATING_ENVELOPES</programType>
    <programStartDate>2021-01-01</programStartDate>
    <programEndDate>2021-12-31</programEndDate>
    <programDispatchPriority>1</programDispatchPriority>
    <vppContract>false</vppContract>
    <supportedControlTypeList>
      <supportedControlType>opModMaxLimW</supportedControlType>
    </supportedControlTypeList>
    <programConstraintList>
      <programConstraint>
        <programConstraintType>1</programConstraintType>
        <programConstraintStart>0</programConstraintStart>
        <programConstraintEnd>23</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>2</programConstraintType>
        <programConstraintStart>mon</programConstraintStart>
        <programConstraintEnd>sun</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>3</programConstraintType>
      </programConstraint>
      <programConstraint>
        <programConstraintType>4</programConstraintType>
        <programConstraintStart>jan1</programConstraintStart>
        <programConstraintEnd>dec31</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>5</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>6</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>7</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>8</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>9</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>10</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>11</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>12</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>13</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
    </programConstraintList>
  </Program>
</ProgramList>"""  # noqa: E501

        single_payload.program.program_type = ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES
        single_payload.program.control_type = DOEControlType.DER_EXPORT_LIMIT

        program_XML = BuildProgramXML.build([single_payload])
        self.assert_xml_str_equals(xml_str, program_XML)

    def test_create_DEMAND_MANAGEMENT_program_xml(self, single_payload):
        xml_str = """
<ProgramList action="add" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="com:ge:ieee2030:registration:rest:ext:dto">
  <Program>
    <programId>1</programId>
    <programName>Test Program</programName>
    <programType>DEMAND_MANAGEMENT</programType>
    <programStartDate>2021-01-01</programStartDate>
    <programEndDate>2021-12-31</programEndDate>
    <programDispatchPriority>1</programDispatchPriority>
    <vppContract>true</vppContract>
    <supportedControlTypeList>
      <supportedControlType>opModFixedW</supportedControlType>
    </supportedControlTypeList>
    <programConstraintList>
      <programConstraint>
        <programConstraintType>1</programConstraintType>
        <programConstraintStart>0</programConstraintStart>
        <programConstraintEnd>23</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>2</programConstraintType>
        <programConstraintStart>mon</programConstraintStart>
        <programConstraintEnd>sun</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>3</programConstraintType>
      </programConstraint>
      <programConstraint>
        <programConstraintType>4</programConstraintType>
        <programConstraintStart>jan1</programConstraintStart>
        <programConstraintEnd>dec31</programConstraintEnd>
      </programConstraint>
      <programConstraint>
        <programConstraintType>5</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>6</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>7</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>8</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>9</programConstraintType>
        <programConstraintLimit>60</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>10</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>11</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>12</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
      <programConstraint>
        <programConstraintType>13</programConstraintType>
        <programConstraintLimit>1</programConstraintLimit>
      </programConstraint>
    </programConstraintList>
  </Program>
</ProgramList>"""  # noqa: E501

        single_payload.program.program_type = ProgramTypeEnum.DEMAND_MANAGEMENT
        program_XML = BuildProgramXML.build([single_payload])
        self.assert_xml_str_equals(xml_str, program_XML)
