from datetime import datetime
from http import HTTPStatus

import pytest

from pm.modules.progmgmt.enums import DispatchTypeEnum
from pm.tests_acceptance.program.base import TestProgramBase
from shared.enums import ControlOptionsEnum


class TestPM368(TestProgramBase):
    """As a utility, I need to create a new generic program"""

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        name="name",
                        program_type="GENERIC",
                        start_date=datetime(2022, 9, 1).isoformat(),
                        end_date=datetime(2023, 9, 1).isoformat(),
                        program_priority="P0",
                        availability_type="SERVICE_WINDOWS",
                        check_der_eligibility=True,
                        define_contractual_target_capacity=True,
                        notification_type="SMS_EMAIL",
                    ),
                    avail_operating_months=dict(
                        jan=True,
                        feb=False,
                        mar=False,
                        apr=False,
                        may=False,
                        jun=False,
                        jul=False,
                        aug=False,
                        sep=False,
                        oct=False,
                        nov=False,
                        dec=False,
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
                    resource_eligibility_criteria=dict(
                        max_real_power_rating=10.0,
                        min_real_power_rating=2.0,
                    ),
                    dispatch_max_opt_outs=[
                        dict(
                            timeperiod="DAY",
                            value=10,
                        ),
                        dict(
                            timeperiod="MONTH",
                            value=10,
                        ),
                    ],
                    dispatch_notifications=[dict(text="test", lead_time=10)],
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
                    general_fields=dict(name="name", program_type="GENERIC"),
                ),
                id="min-required-fields",
            ),
        ],
    )
    def test_create_program_success(self, client, db_session, body):
        """Given a generic program payload is valid
        When the payload is submitted to the api
        Then the response received is 200
        And the new program will be in the database
        """
        resp = client.post("/api/program/", json=body)
        assert resp.status_code == HTTPStatus.CREATED

    @pytest.mark.parametrize(
        "body,code",
        [
            pytest.param(
                dict(
                    general_fields=dict(name="name", program_type="GENERIC"),
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
                            start_hour=2,
                            end_hour=11,
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
                HTTPStatus.BAD_REQUEST,
                id="service-window-err",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        name="name",
                        program_type="GENERIC",
                        start_date=datetime(2022, 9, 1).isoformat(),
                        end_date=datetime(2022, 8, 1).isoformat(),
                    ),
                ),
                HTTPStatus.UNPROCESSABLE_ENTITY,
                id="start-end-err",
            ),
        ],
    )
    def test_create_program_error(self, client, db_session, body, code):
        """Given a generic program payload is invalid
        When the payload is submitted to the api
        Then the response received is 400
        And the new program will not be in the database

        Given a program exists in the database
        When a new generic program is created with the same name
        Then the response received is 400
        And the new program will not be in the database
        """
        resp = client.post("/api/program/", json=body)
        assert resp.status_code == code

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                dict(
                    general_fields=dict(name="name", program_type="GENERIC"),
                    control_options=[
                        ControlOptionsEnum.OP_MOD_CONNECT.name,
                        ControlOptionsEnum.OP_MOD_FIXED_PF_ABSORB_W.name,
                        ControlOptionsEnum.OP_MOD_HVRT_MUST_TRIP.name,
                    ],
                    dispatch_type=DispatchTypeEnum.API.name,
                    track_event=True,
                )
            ),
        ],
    )
    def test_create_program_generic_options(self, client, db_session, body):
        resp = client.post("/api/program/", json=body)
        assert resp.status_code == 201
        programs = self._get_programs(db_session)

        for control_type in programs[0].control_options:
            assert control_type.name in body["control_options"]

        assert len(programs) == 1
        assert programs[0].dispatch_type.name == body["dispatch_type"]
        assert programs[0].track_event == body["track_event"]

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                dict(
                    general_fields=dict(name="name", program_type="GENERIC"),
                    control_options="bad value",
                    dispatch_type="bad value",
                    track_event=True,
                )
            ),
        ],
    )
    def test_create_program_generic_options_fail(self, client, db_session, body):
        resp = client.post("/api/program/", json=body)
        assert resp.status_code == 422
        programs = self._get_programs(db_session)
        assert len(programs) == 0
