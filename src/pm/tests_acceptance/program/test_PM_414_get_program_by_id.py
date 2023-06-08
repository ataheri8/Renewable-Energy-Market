from http import HTTPStatus

from pm.modules.progmgmt.enums import ProgramStatus
from pm.tests import factories


class TestPM414:
    """As a utility, I need to be able to retrieve full program details by program ID"""

    def test_get_program(self, client, db_session):
        """BDD PM-415

        Given a program already exists
        When I want to get the program details
        Then the program should be returned with all the fields
        """
        timestep = 1
        time_horizon = 10
        program = factories.DynamicOperatingEnvelopesProgram(
            schedule_timestep_mins=timestep, schedule_time_horizon_number=time_horizon
        )
        program_id = program.id

        response = client.get(f"/api/program/{program_id}")
        program = response.json
        assert program
        assert response.status_code == HTTPStatus.OK
        assert program["id"] == program_id
        # Checking relational fields still exist as an empty value, checking one with a value
        assert len(program["dispatch_max_opt_outs"]) == 1
        assert program["schedule_time_horizon_number"] == time_horizon
        assert program["schedule_timestep_mins"] == timestep

    def test_get_program_archived_error(self, client, db_session):
        """BDD PM-683

        Given a program already exists
            And the program is archived
        When I want to get the program details
        Then the program should not appear
        """
        program = factories.ProgramFactory(status=ProgramStatus.ARCHIVED)
        program_id = program.id

        response = client.get(f"/api/program/{program_id}")

        assert response.status_code == HTTPStatus.BAD_REQUEST
