from dataclasses import asdict
from datetime import datetime
from http import HTTPStatus

import pendulum
import pytest

from pm.modules.progmgmt.enums import ProgramStatus
from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase


class TestPM426(TestProgramBase):
    # TODO BDDs inconsistent with the test cases in ticket
    """As a utility, I need to modify a program"""

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        name="name",
                        start_date=datetime(2022, 9, 1).isoformat(),
                        end_date=datetime(2023, 9, 1).isoformat(),
                        program_priority="P0",
                        availability_type="SERVICE_WINDOWS",
                        check_der_eligibility=True,
                        define_contractual_target_capacity=True,
                        notification_type="SMS_EMAIL",
                    ),
                    dispatch_constraints=dict(
                        event_duration_constraint=dict(
                            min=1,
                            max=2,
                        ),
                        cumulative_event_duration=dict(
                            MONTH=dict(
                                min=1,
                                max=2,
                            ),
                            DAY=dict(
                                min=1,
                                max=2,
                            ),
                        ),
                        max_number_of_events_per_timeperiod=dict(
                            MONTH=2,
                            DAY=10,
                        ),
                    ),
                    avail_service_windows=[
                        dict(
                            start_hour=1,
                            end_hour=10,
                            mon=True,
                            tue=True,
                            wed=True,
                            thu=True,
                            fri=True,
                            sat=True,
                            sun=True,
                        ),
                        dict(
                            start_hour=10,
                            end_hour=12,
                            mon=True,
                            tue=True,
                            wed=True,
                            thu=True,
                            fri=True,
                            sat=True,
                            sun=True,
                        ),
                    ],
                ),
                id="all-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(name="name"),
                ),
                id="min-required-fields",
            ),
        ],
    )
    def test_save_program(self, client, db_session, body):
        """Given a valid program_id
        And valid values to partially replace program values
        When user calls PATCH endpoint
        Then response received is 204
        """
        program = factories.GenericProgramFactory()
        program_id = program.id
        resp = client.patch(f"/api/program/{program_id}", json=body)
        assert resp.status_code == HTTPStatus.OK
        program = self._get_program(db_session, program_id)
        assert program
        assert program.name == body["general_fields"]["name"]
        if body.get("avail_service_windows"):
            assert len(program.avail_service_windows) == len(body.get("avail_service_windows"))
        if body.get("dispatch_constraints"):
            print(program.dispatch_constraints)
            assert asdict(program.dispatch_constraints) == body.get("dispatch_constraints")

    def test_save_program_archived_error(self, client, db_session):
        """Given a program doesn't in the database
        When user archives the program
        Then response received is 404
        """
        program = factories.ProgramFactory(status=ProgramStatus.ARCHIVED)
        resp = client.patch(
            f"/api/program/{program.id}",
            json=dict(
                general_fields=dict(program_priority="P5"),
            ),
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_save_program_ended_error(self, client, db_session):
        """Given a program exists in the database
        When user updates the program
        And the program end date has passed
        Then response received is 404
        """
        program = factories.ProgramFactory(end_date=pendulum.datetime(2020, 1, 1))
        resp = client.patch(
            f"/api/program/{program.id}",
            json=dict(
                general_fields=dict(program_priority="P5"),
            ),
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_save_program_no_program_exists(self, client, db_session):
        """Given a program doesn't exist in the database
        When user updates the program
        Then response received is 404
        """
        resp = client.patch(
            f"/api/program/12345",  # noqa:  F541
            json=dict(
                general_fields=dict(name="name", program_type="GENERIC"),
            ),
        )
        assert resp.status_code == HTTPStatus.NOT_FOUND
