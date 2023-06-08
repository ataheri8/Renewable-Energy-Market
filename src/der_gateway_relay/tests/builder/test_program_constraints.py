import pytest

from der_gateway_relay.builders.program_constraints import (
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
from der_gateway_relay.tests.builder.mixins import AssertXMLEqualsMixin
from shared.validators import der_gateway_data as program_data


class TestBuildProgramConstraintOneXML(AssertXMLEqualsMixin):
    def test_create_one_constraint_xml(self, single_payload):
        """
        Test that XML is generated in correct format with given values
        """
        xml_str = """
<programConstraint>
  <programConstraintType>1</programConstraintType>
  <programConstraintStart>0</programConstraintStart>
  <programConstraintEnd>23</programConstraintEnd>
</programConstraint>"""

        constraint_one = BuildProgramConstraintTypeOne.build_constraint(single_payload)
        assert len(constraint_one) == 1
        self.assert_xml_equals(xml_str, constraint_one[0])

    def test_create_multiple_constraint_xml(self, single_payload: program_data.DerGatewayProgram):
        """
        Test that XML is generated in correct format with given values
        """
        xml_str_1 = """
<programConstraint>
  <programConstraintType>1</programConstraintType>
  <programConstraintStart>0</programConstraintStart>
  <programConstraintEnd>23</programConstraintEnd>
</programConstraint>"""
        xml_str_2 = """
<programConstraint>
  <programConstraintType>1</programConstraintType>
  <programConstraintStart>3</programConstraintStart>
  <programConstraintEnd>13</programConstraintEnd>
</programConstraint>"""

        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=23,
                mon=True,
                tue=True,
                wed=False,
                thu=False,
                fri=False,
                sat=False,
                sun=False,
            ),
            program_data._AvailServiceWindows(
                id=2,
                start_hour=3,
                end_hour=13,
                mon=False,
                tue=False,
                wed=True,
                thu=True,
                fri=True,
                sat=True,
                sun=True,
            ),
        ]
        constraint_one = BuildProgramConstraintTypeOne.build_constraint(single_payload)
        assert len(constraint_one) == 2
        self.assert_xml_equals(xml_str_1, constraint_one[0])
        self.assert_xml_equals(xml_str_2, constraint_one[1])

    def test_out_of_bound_values(self, single_payload: program_data.DerGatewayProgram):
        """
        Test that constraint start and end times aren't out of bounds or negative
        Invalid values result in nothing being generated
        """
        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=-23,
                mon=True,
                tue=False,
                wed=False,
                thu=False,
                fri=False,
                sat=False,
                sun=False,
            ),
            program_data._AvailServiceWindows(
                id=2,
                start_hour=-3,
                end_hour=13,
                mon=False,
                tue=True,
                wed=False,
                thu=False,
                fri=False,
                sat=False,
                sun=False,
            ),
            program_data._AvailServiceWindows(
                id=3,
                start_hour=3,
                end_hour=28,
                mon=False,
                tue=False,
                wed=True,
                thu=False,
                fri=False,
                sat=False,
                sun=False,
            ),
            program_data._AvailServiceWindows(
                id=4,
                start_hour=33,
                end_hour=20,
                mon=False,
                tue=False,
                wed=False,
                thu=True,
                fri=False,
                sat=False,
                sun=False,
            ),
            program_data._AvailServiceWindows(
                id=5,
                start_hour=33,
                end_hour=44,
                mon=False,
                tue=False,
                wed=False,
                thu=False,
                fri=True,
                sat=False,
                sun=False,
            ),
        ]
        constraint_one_negative_end_hour = BuildProgramConstraintTypeOne.build_constraint(
            single_payload
        )
        assert constraint_one_negative_end_hour == []


class TestBuildProgramConstraintTwoXML(AssertXMLEqualsMixin):
    def test_create_constraint_two_xml(self, single_payload: program_data.DerGatewayProgram):
        """
        Test that XML is generated in correct format with given values
        """
        xml_str = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>mon</programConstraintStart>
  <programConstraintEnd>sun</programConstraintEnd>
</programConstraint>"""
        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        assert len(constraint_two) == 1
        self.assert_xml_equals(xml_str, constraint_two[0])

    def test_create_constraint_two_xml_monday_to_sunday(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated with correct operational days from monday to sunday
        """
        xml_str = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>mon</programConstraintStart>
  <programConstraintEnd>sun</programConstraintEnd>
</programConstraint>"""

        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        assert len(constraint_two) == 1
        self.assert_xml_equals(xml_str, constraint_two[0])

    def test_create_constraint_two_xml_scattered_operational_days(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated with correct operational days from monday to tuesday and
        """
        xml_str_1 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>mon</programConstraintStart>
  <programConstraintEnd>tue</programConstraintEnd>
</programConstraint>"""
        xml_str_2 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>thu</programConstraintStart>
  <programConstraintEnd>thu</programConstraintEnd>
</programConstraint>"""
        xml_str_3 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>sat</programConstraintStart>
  <programConstraintEnd>sun</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=23,
                mon=True,
                tue=True,
                wed=False,
                thu=True,
                fri=False,
                sat=True,
                sun=True,
            )
        ]
        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        assert len(constraint_two) == 3
        self.assert_xml_equals(xml_str_1, constraint_two[0])
        self.assert_xml_equals(xml_str_2, constraint_two[1])
        self.assert_xml_equals(xml_str_3, constraint_two[2])

    def test_create_constraint_two_xml_scattered_operational_days_with_no_overlap(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated with correct operational days from monday to tuesday and
        """
        xml_str_1 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>mon</programConstraintStart>
  <programConstraintEnd>mon</programConstraintEnd>
</programConstraint>"""
        xml_str_2 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>wed</programConstraintStart>
  <programConstraintEnd>wed</programConstraintEnd>
</programConstraint>"""
        xml_str_3 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>fri</programConstraintStart>
  <programConstraintEnd>fri</programConstraintEnd>
</programConstraint>"""
        xml_str_4 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>sun</programConstraintStart>
  <programConstraintEnd>sun</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=23,
                mon=True,
                tue=False,
                wed=True,
                thu=False,
                fri=True,
                sat=False,
                sun=True,
            )
        ]
        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        assert len(constraint_two) == 4
        self.assert_xml_equals(xml_str_1, constraint_two[0])
        self.assert_xml_equals(xml_str_2, constraint_two[1])
        self.assert_xml_equals(xml_str_3, constraint_two[2])
        self.assert_xml_equals(xml_str_4, constraint_two[3])

    def test_create_constraint_two_xml_scattered_operational_days_with_no_overlap_opposite_days(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated with correct operational days from monday to tuesday and
        """
        xml_str_1 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>tue</programConstraintStart>
  <programConstraintEnd>tue</programConstraintEnd>
</programConstraint>"""
        xml_str_2 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>thu</programConstraintStart>
  <programConstraintEnd>thu</programConstraintEnd>
</programConstraint>"""
        xml_str_3 = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>sat</programConstraintStart>
  <programConstraintEnd>sat</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=23,
                mon=False,
                tue=True,
                wed=False,
                thu=True,
                fri=False,
                sat=True,
                sun=False,
            )
        ]
        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        assert len(constraint_two) == 3
        self.assert_xml_equals(xml_str_1, constraint_two[0])
        self.assert_xml_equals(xml_str_2, constraint_two[1])
        self.assert_xml_equals(xml_str_3, constraint_two[2])

    def test_create_constraint_two_xml_scattered_operational_days_with_only_one_range(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated with correct operational days from monday to tuesday and
        """
        xml_str = """
<programConstraint>
  <programConstraintType>2</programConstraintType>
  <programConstraintStart>tue</programConstraintStart>
  <programConstraintEnd>thu</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=23,
                mon=False,
                tue=True,
                wed=True,
                thu=True,
                fri=False,
                sat=False,
                sun=False,
            )
        ]
        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_two[0])

    def test_create_constraint_two_xml_no_operational_days_with_only_one_range(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated with correct operational days from monday to tuesday and
        """
        single_payload.program.avail_service_windows = [
            program_data._AvailServiceWindows(
                id=1,
                start_hour=0,
                end_hour=23,
                mon=False,
                tue=False,
                wed=False,
                thu=False,
                fri=False,
                sat=False,
                sun=False,
            )
        ]
        constraint_two = BuildProgramConstraintTypeTwo.build_constraint(single_payload)
        assert constraint_two == []


class TestBuildProgramConstraintThreeXML(AssertXMLEqualsMixin):
    def test_create_constraint_three_xml(self, single_payload: program_data.DerGatewayProgram):
        """
        Test that XML is generated in correct format with given values
        """
        xml_str = """
<programConstraint>
  <programConstraintType>3</programConstraintType>
</programConstraint>"""
        constraint_three = BuildProgramConstraintTypeThree.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_three[0])

    def test_create_constraint_three_xml_with_multiple_holidays(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        Only a single type three constraint should be generated in XML
         even if multiple NERC holidays exist
        """
        xml_str = """
<programConstraint>
  <programConstraintType>3</programConstraintType>
</programConstraint>"""
        single_payload.program.holiday_exclusions = program_data._HolidayExclusions.from_dict(
            {
                "calendars": [
                    {
                        "mrid": "mrid",
                        "timezone": "America/Los_Angeles",
                        "year": 2021,
                        "events": [
                            {
                                "startDate": "2021-01-01",
                                "endDate": "2021-01-01",
                                "name": "New Year's Day",
                                "category": "National Holiday",
                                "substitutionDate": "2021-01-01",
                            },
                            {
                                "startDate": "2021-05-01",
                                "endDate": "2021-05-01",
                                "name": "Memorial Day",
                                "category": "National Holiday",
                                "substitutionDate": "2021-05-01",
                            },
                            {
                                "startDate": "2021-07-01",
                                "endDate": "2021-07-01",
                                "name": "Independence Day",
                                "category": "National Holiday",
                                "substitutionDate": "2021-07-01",
                            },
                        ],
                    }
                ]
            }
        )
        constraint_three = BuildProgramConstraintTypeThree.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_three[0])

    def test_create_constraint_three_xml_with_no_return(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        No values should return since there are no National holidays in payload
        """
        single_payload.program.holiday_exclusions = program_data._HolidayExclusions.from_dict(
            {
                "calendars": [
                    {
                        "mrid": "mrid",
                        "timezone": "America/Los_Angeles",
                        "year": 2021,
                        "events": [
                            {
                                "startDate": "2021-01-02",
                                "endDate": "2021-01-02",
                                "name": "Random Day 1",
                                "category": "Unimportant Day 1",
                                "substitutionDate": "2021-01-02",
                            },
                            {
                                "startDate": "2021-05-02",
                                "endDate": "2021-05-02",
                                "name": "Random Day 2",
                                "category": "Unimportant Day 2",
                                "substitutionDate": "2021-05-02",
                            },
                            {
                                "startDate": "2021-07-03",
                                "endDate": "2021-07-03",
                                "name": "Random Day 3",
                                "category": "Unimportant Day 3",
                                "substitutionDate": "2021-07-03",
                            },
                        ],
                    }
                ]
            }
        )
        constraint_three = BuildProgramConstraintTypeThree.build_constraint(single_payload)
        assert constraint_three == []


class TestBuildProgramConstraintFourXML(AssertXMLEqualsMixin):
    def test_create_constraint_four_xml(self, single_payload: program_data.DerGatewayProgram):
        """
        Test that XML is generated in correct format with given values
        """
        xml_str = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jan1</programConstraintStart>
  <programConstraintEnd>dec31</programConstraintEnd>
</programConstraint>"""
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_four[0])

    def test_create_constraint_four_xml_current_year(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        using the year 2023, operational days from monday to sunday, and january to december
        """
        xml_str = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jan1</programConstraintStart>
  <programConstraintEnd>dec31</programConstraintEnd>
</programConstraint>"""
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_four[0])

    def test_create_constraint_four_xml_current_year_consecutive_days(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        using the year 2023, operational months from january to december

        """
        xml_str = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jan1</programConstraintStart>
  <programConstraintEnd>dec31</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_operating_months = (
            program_data._AvailOperatingMonths.from_dict(
                {
                    "id": 1,
                    "jan": True,
                    "feb": True,
                    "mar": True,
                    "apr": True,
                    "may": True,
                    "jun": True,
                    "jul": True,
                    "aug": True,
                    "sep": True,
                    "oct": True,
                    "nov": True,
                    "dec": True,
                }
            )
        )
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_four[0])

    def test_create_constraint_four_xml_current_year_scattered_days_consecutive_months(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        using the year 2023, scatterd operational days, and june to september

        """
        xml_str = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jun1</programConstraintStart>
  <programConstraintEnd>sep30</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_operating_months = (
            program_data._AvailOperatingMonths.from_dict(
                {
                    "id": 1,
                    "jan": False,
                    "feb": False,
                    "mar": False,
                    "apr": False,
                    "may": False,
                    "jun": True,
                    "jul": True,
                    "aug": True,
                    "sep": True,
                    "oct": False,
                    "nov": False,
                    "dec": False,
                }
            )
        )
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        self.assert_xml_equals(xml_str, constraint_four[0])

    def test_create_constraint_four_xml_current_year_scattered_days_scattered_months(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        using the year 2023, scatterd operational days, and scattered operational months

        """
        xml_str_1 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jan1</programConstraintStart>
  <programConstraintEnd>jan31</programConstraintEnd>
</programConstraint>"""
        xml_str_2 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>mar1</programConstraintStart>
  <programConstraintEnd>apr30</programConstraintEnd>
</programConstraint>"""
        xml_str_3 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jun1</programConstraintStart>
  <programConstraintEnd>jul31</programConstraintEnd>
</programConstraint>"""
        xml_str_4 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>sep1</programConstraintStart>
  <programConstraintEnd>oct31</programConstraintEnd>
</programConstraint>"""
        xml_str_5 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>dec1</programConstraintStart>
  <programConstraintEnd>dec31</programConstraintEnd>
</programConstraint>"""
        single_payload.program.avail_operating_months = (
            program_data._AvailOperatingMonths.from_dict(
                {
                    "id": 1,
                    "jan": True,
                    "feb": False,
                    "mar": True,
                    "apr": True,
                    "may": False,
                    "jun": True,
                    "jul": True,
                    "aug": False,
                    "sep": True,
                    "oct": True,
                    "nov": False,
                    "dec": True,
                }
            )
        )
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        assert len(constraint_four) == 5
        self.assert_xml_equals(xml_str_1, constraint_four[0])
        self.assert_xml_equals(xml_str_2, constraint_four[1])
        self.assert_xml_equals(xml_str_3, constraint_four[2])
        self.assert_xml_equals(xml_str_4, constraint_four[3])
        self.assert_xml_equals(xml_str_5, constraint_four[4])

    def test_create_constraint_four_xml_current_year_no_days_consecutive_months(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        using the year 2023, no operational days, and scattered operational months

        """
        xml_str_1 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jan1</programConstraintStart>
  <programConstraintEnd>jan31</programConstraintEnd>
</programConstraint>"""
        xml_str_2 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>mar1</programConstraintStart>
  <programConstraintEnd>apr30</programConstraintEnd>
</programConstraint>"""
        xml_str_3 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>jun1</programConstraintStart>
  <programConstraintEnd>jul31</programConstraintEnd>
</programConstraint>"""
        xml_str_4 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>sep1</programConstraintStart>
  <programConstraintEnd>oct31</programConstraintEnd>
</programConstraint>"""
        xml_str_5 = """
<programConstraint>
  <programConstraintType>4</programConstraintType>
  <programConstraintStart>dec1</programConstraintStart>
  <programConstraintEnd>dec31</programConstraintEnd>
</programConstraint>"""
        single_payload.program.start_date = "2023-01-01"
        single_payload.program.end_date = "2023-12-31"
        single_payload.program.avail_operating_months = (
            program_data._AvailOperatingMonths.from_dict(
                {
                    "id": 1,
                    "jan": True,
                    "feb": False,
                    "mar": True,
                    "apr": True,
                    "may": False,
                    "jun": True,
                    "jul": True,
                    "aug": False,
                    "sep": True,
                    "oct": True,
                    "nov": False,
                    "dec": True,
                }
            )
        )
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        assert len(constraint_four) == 5
        self.assert_xml_equals(xml_str_1, constraint_four[0])
        self.assert_xml_equals(xml_str_2, constraint_four[1])
        self.assert_xml_equals(xml_str_3, constraint_four[2])
        self.assert_xml_equals(xml_str_4, constraint_four[3])
        self.assert_xml_equals(xml_str_5, constraint_four[4])

    def test_create_constraint_four_xml_current_year_no_days_no_months(
        self, single_payload: program_data.DerGatewayProgram
    ):
        """
        Test that XML is generated in correct format with given values
        using the year 2023, no operational days, and scattered operational months

        """
        single_payload.program.start_date = "2023-01-01"
        single_payload.program.end_date = "2023-12-31"
        single_payload.program.avail_operating_months = (
            program_data._AvailOperatingMonths.from_dict(
                {
                    "id": 1,
                    "jan": False,
                    "feb": False,
                    "mar": False,
                    "apr": False,
                    "may": False,
                    "jun": False,
                    "jul": False,
                    "aug": False,
                    "sep": False,
                    "oct": False,
                    "nov": False,
                    "dec": False,
                }
            )
        )
        constraint_four = BuildProgramConstraintTypeFour.build_constraint(single_payload)
        assert constraint_four == []


class TestBuildProgramXMLConstraintsFiveToTwelve(AssertXMLEqualsMixin):
    @pytest.mark.parametrize(
        "constraint_type,xml",
        [
            (
                BuildProgramConstraintTypeFive,
                """
<programConstraint>
  <programConstraintType>5</programConstraintType>
  <programConstraintLimit>1</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeSix,
                """
<programConstraint>
  <programConstraintType>6</programConstraintType>
  <programConstraintLimit>60</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeSeven,
                """
<programConstraint>
  <programConstraintType>7</programConstraintType>
  <programConstraintLimit>60</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeEight,
                """
<programConstraint>
  <programConstraintType>8</programConstraintType>
  <programConstraintLimit>60</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeNine,
                """
<programConstraint>
  <programConstraintType>9</programConstraintType>
  <programConstraintLimit>60</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeTen,
                """
<programConstraint>
  <programConstraintType>10</programConstraintType>
  <programConstraintLimit>1</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeEleven,
                """
<programConstraint>
  <programConstraintType>11</programConstraintType>
  <programConstraintLimit>1</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeTwelve,
                """
<programConstraint>
  <programConstraintType>12</programConstraintType>
  <programConstraintLimit>1</programConstraintLimit>
</programConstraint>""",
            ),
            (
                BuildProgramConstraintTypeThirteen,
                """
<programConstraint>
  <programConstraintType>13</programConstraintType>
  <programConstraintLimit>1</programConstraintLimit>
</programConstraint>""",
            ),
        ],
    )
    def test_create_type_five_through_thirteen_constraint_xml(
        self, constraint_type, xml, single_payload
    ):
        """
        Test that XML is generated in correct format with given values
        """
        constraint = constraint_type.build_constraint(single_payload)
        self.assert_xml_equals(xml, constraint[0])
