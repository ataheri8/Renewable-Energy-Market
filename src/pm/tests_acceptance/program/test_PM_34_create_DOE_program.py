from http import HTTPStatus

from sqlalchemy import select

from pm.modules.progmgmt.enums import (
    DOECalculationFrequency,
    DOELimitType,
    ScheduleTimeperiod,
)
from pm.modules.progmgmt.models.program import DynamicOperatingEnvelopesProgram
from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase
from shared.enums import ControlOptionsEnum, DOEControlType


class TestPM34(TestProgramBase):
    """[Program Setup] As a utility, I need to create a DOE program with specific DOE fields"""

    def test_create_doe_program(self, client, db_session):
        """Given I want to create a DOE program
        When I create a DOE program
        Then I should be able to create one with the specific DOE fields
        """
        body = dict(
            general_fields=dict(
                name="name",
                program_type="DYNAMIC_OPERATING_ENVELOPES",
            ),
            control_options=[ControlOptionsEnum.CSIP_AUS.name],
            dynamic_operating_envelope_fields=dict(
                limit_type="REACTIVE_POWER",
                calculation_frequency="DAILY",
                control_type=[DOEControlType.CONNECTION_POINT_EXPORT_LIMIT.name],
                schedule_time_horizon_timeperiod="MINUTES",
                schedule_time_horizon_number=10,
                schedule_timestep_mins=10,
            ),
        )
        resp = client.post("/api/program/", json=body)
        assert resp.status_code == 201

        with db_session() as session:
            stmt = select(DynamicOperatingEnvelopesProgram)
            p: DynamicOperatingEnvelopesProgram = session.execute(stmt).scalar_one_or_none()
            assert p is not None
            assert p.limit_type == DOELimitType.REACTIVE_POWER
            assert p.calculation_frequency == DOECalculationFrequency.DAILY
            assert p.control_type == [DOEControlType.CONNECTION_POINT_EXPORT_LIMIT]
            assert p.schedule_time_horizon_timeperiod == ScheduleTimeperiod.MINUTES
            assert p.schedule_time_horizon_number == 10
            assert p.schedule_timestep_mins == 10

    def test_update_doe_program_with_specific_fields(self, client, db_session):
        """Given I want to create a DOE program
        When I create a DOE program
        Then I should be able to create one with the specific DOE fields

        Given I want to create or update a non DOE program
        When I try to create or update with DOE specific fields
        Then those fields should not be saved
        """
        # dynamic operating envelopes should save
        program = factories.DynamicOperatingEnvelopesProgram()
        program_1_id = program.id
        body = dict(
            dynamic_operating_envelope_fields=dict(
                limit_type="REACTIVE_POWER",
                calculation_frequency="DAILY",
                control_type=[],
                schedule_time_horizon_timeperiod="MINUTES",
                schedule_time_horizon_number=10,
                schedule_timestep_mins=10,
            )
        )
        resp = client.patch(f"/api/program/{program_1_id}", json=body)
        assert resp.status_code == HTTPStatus.OK

        p = self._get_program(db_session, program_1_id)
        assert p is not None
        assert p.limit_type == DOELimitType.REACTIVE_POWER
        assert p.calculation_frequency == DOECalculationFrequency.DAILY
        assert p.control_type == []
        assert p.schedule_time_horizon_timeperiod == ScheduleTimeperiod.MINUTES
        assert p.schedule_time_horizon_number == 10
        assert p.schedule_timestep_mins == 10
        # generic should not save
        program = factories.GenericProgramFactory()
        program_2_id = program.id
        resp = client.patch(f"/api/program/{program_2_id}", json=body)
        assert resp.status_code == HTTPStatus.OK

        p = self._get_program(db_session, program_2_id)
        assert p is not None
        assert p.limit_type is None
        assert p.calculation_frequency is None
        assert p.control_type is None
        assert p.schedule_time_horizon_timeperiod is None
        assert p.schedule_time_horizon_number is None
        assert p.schedule_timestep_mins is None
