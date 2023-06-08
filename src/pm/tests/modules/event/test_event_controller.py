from datetime import date
from decimal import Decimal
from unittest import mock
from uuid import uuid4

import pendulum
import pytest
from freezegun import freeze_time

from pm.modules.enrollment.enums import ContractStatus
from pm.modules.event_tracking.controller import CreateDerResponseDict, EventController
from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.event_tracking.models.der_response import DerResponse
from pm.modules.progmgmt.enums import ProgramTimePeriod
from pm.modules.progmgmt.models.dispatch_opt_out import DispatchOptOut
from pm.modules.progmgmt.models.program import Constraints, DemandManagementConstraints
from pm.tests import factories


class TestEventController:
    def _get_all(self, db_session, Entity) -> list:
        with db_session() as session:
            return session.query(Entity).all()

    def test_create_der_dispatch(self, db_session):
        no_of_records = 1000
        data = []
        factories.ContractFactory(id=1)
        for i in range(1, no_of_records + 1):
            dispatch_info = dict(
                event_id=f"event-{i}",
                start_date_time=1635489900,
                end_date_time=1635497100,
                event_status="scheduled",
                control_command="1.00",
                control_type="kW % Rated Capacity",
                contract_id=1,
                control_id="B94E28E2C65547B3B1F9C096D4F8952B",
            )
            data.append(dispatch_info)
            dispatch_info = dict(
                event_id=f"event-{i}2",
                start_date_time=1635489900,
                end_date_time=1635497100,
                event_status="scheduled",
                control_command="1.00",
                control_type="kW % Rated Capacity",
                contract_id=3,
                control_id="B94E28E2C65547B3B1F9C096D4F8952B",
            )
            data.append(dispatch_info)
            dispatch_info = dict(
                event_id=f"event-{i}3",
                start_date_time=1635489900,
                end_date_time=1635497100,
                event_status="scheduled",
                control_command="1.00",
                control_type="kW % Rated Capacity",
                contract_id=2,
                control_id="B94E28E2C65547B3B1F9C096D4F8952B",
            )
            data.append(dispatch_info)

        EventController().create_der_dispatch(data)

        dispatches = self._get_all(db_session, DerDispatch)
        assert len(dispatches) == 1000
        for i, d in enumerate(dispatches):
            assert d.event_id == f"event-{i+1}"
            assert d.control_id == "B94E28E2C65547B3B1F9C096D4F8952B"
            assert d.contract_id == 1
            assert d.max_total_energy == Decimal("120")
            assert d.cumulative_event_duration_mins == 120

    def test_create_dispatch_no_contract(self, db_session):
        event_id = "1"
        data = [
            dict(
                event_id=event_id,
                start_date_time=1635489900,
                end_date_time=1635497100,
                event_status="scheduled",
                control_target="77.77",
                control_type="kW % Rated Capacity",
                contract_id=1,
                control_id="B94E28E2C65547B3B1F9C096D4F8952B",
            )
        ]
        EventController().create_der_dispatch(data)

        dispatches = self._get_all(db_session, DerDispatch)
        assert len(dispatches) == 0

    @pytest.mark.parametrize(
        "data,skip_contracts_for_half",
        [
            pytest.param(
                [
                    CreateDerResponseDict(
                        der_id="9101080001",
                        der_response_status=4,
                        der_response_time=pendulum.now(tz="UTC"),
                        control_id=f"{uuid4()}",
                        is_opt_out=True,
                    ),
                    CreateDerResponseDict(
                        der_id="9101080002",
                        der_response_status=4,
                        der_response_time=pendulum.now(tz="UTC"),
                        control_id=f"{uuid4()}",
                        is_opt_out=True,
                    ),
                ],
                False,
                id="all_opt_out",
            ),
            pytest.param(
                [
                    CreateDerResponseDict(
                        der_id="9101080001",
                        der_response_status=4,
                        der_response_time=pendulum.now(tz="UTC"),
                        control_id=f"{uuid4()}",
                        is_opt_out=True,
                    ),
                    CreateDerResponseDict(
                        der_id="9101080002",
                        der_response_status=4,
                        der_response_time=pendulum.now(tz="UTC"),
                        control_id=f"{uuid4()}",
                        is_opt_out=False,
                    ),
                ],
                True,
                id="half_opt_out",
            ),
            pytest.param(
                [
                    CreateDerResponseDict(
                        der_id="9101080001",
                        der_response_status=4,
                        der_response_time=pendulum.now(tz="UTC"),
                        control_id=f"{uuid4()}",
                        is_opt_out=False,
                    ),
                    CreateDerResponseDict(
                        der_id="9101080002",
                        der_response_status=4,
                        der_response_time=pendulum.now(tz="UTC"),
                        control_id=f"{uuid4()}",
                        is_opt_out=False,
                    ),
                ],
                True,
                id="none_opt_out",
            ),
        ],
    )
    def test_create_der_responses(
        self, db_session, data: list[CreateDerResponseDict], skip_contracts_for_half: bool
    ):
        for i, d in enumerate(data):
            der = factories.DerFactory(der_id=d["der_id"])
            if skip_contracts_for_half and i % 2 == 0:
                continue
            factories.ContractFactory(der=der)

        EventController().create_der_response(data)
        responses = self._get_all(db_session, DerResponse)
        expected_number_of_responses = len(data) / 2 if skip_contracts_for_half else len(data)
        assert len(responses) == expected_number_of_responses

        for i, response in enumerate(responses):
            if skip_contracts_for_half and i % 2 == 0:
                continue
            assert response.der_id == data[i]["der_id"]
            assert response.der_response_status == data[i]["der_response_status"]
            assert response.der_response_time == data[i]["der_response_time"]
            assert response.is_opt_out == data[i]["is_opt_out"]

    def test_create_der_response_no_der_enrolled(self, db_session):
        der_id = f"{uuid4()}"
        data = [
            CreateDerResponseDict(
                der_id=der_id,
                der_response_status=4,
                der_response_time=pendulum.now(tz="UTC"),
                control_id=f"{uuid4()}",
                is_opt_out=True,
            )
        ]
        factories.ContractFactory()
        EventController().create_der_response(data)
        responses = self._get_all(db_session, DerResponse)
        assert len(responses) == 0

    def _create_events(
        self,
        db_session,
        number_of_events,
        program,
        make_negative_event_every_n_records=None,
        contract_id=1,
        enrollment_request_id=1,
    ) -> date:
        enrollment_request = factories.EnrollmentRequestFactory(
            id=enrollment_request_id, program=program
        )
        factories.ContractFactory(
            id=contract_id,
            enrollment_request=enrollment_request,
            program=program,
            contract_status=ContractStatus.ACTIVE,
        )

        def create_response(n):
            """Create a response record for every n records"""
            if not make_negative_event_every_n_records:
                return False
            return n % make_negative_event_every_n_records == 0

        with db_session() as session:
            events = []
            now = pendulum.now().subtract(hours=number_of_events)
            for n in range(number_of_events):
                control_id = f"{uuid4()}"

                dispatch_data = dict(
                    event_id=f"{uuid4()}",
                    start_date_time=now,
                    end_date_time=now.add(hours=1),
                    event_status="scheduled",
                    control_command="1.00",
                    control_type="kW % Rated Capacity",
                    contract_id=contract_id,
                    control_id=control_id,
                    cumulative_event_duration_mins=60,
                    max_total_energy=Decimal("60"),
                )

                events.append(DerDispatch(**dispatch_data))
                if create_response(n):
                    response_data = CreateDerResponseDict(
                        der_id=f"{uuid4()}",
                        der_response_status=4,
                        der_response_time=now,
                        control_id=control_id,
                        is_opt_out=True,
                    )
                    events.append(DerResponse(**response_data))

                now = now.add(hours=1)
                session.add_all(events)
                session.commit()
            return now

    @freeze_time("2023-02-24 23:59:00")
    @pytest.mark.parametrize(
        "dispatch_constraints,dispatch_opt_outs,demand_management_constraints,negative_on,expected_result",  # noqa: E501
        [
            pytest.param(
                Constraints.from_dict(
                    dict(
                        event_duration_constraint=dict(
                            min=1,
                            max=2,
                        ),
                        cumulative_event_duration=dict(
                            DAY=dict(
                                min=1 * 60,
                                max=24 * 60,
                            ),
                            WEEK=dict(
                                min=5 * 60,
                                max=140 * 60,
                            ),
                            MONTH=dict(
                                min=10 * 60,
                                max=1000 * 60,
                            ),
                            YEAR=dict(
                                min=10 * 60,
                                max=1200 * 60,
                            ),
                            PROGRAM_DURATION=dict(
                                min=1000 * 60,
                                max=1200 * 60,
                            ),
                        ),
                        max_number_of_events_per_timeperiod=dict(
                            DAY=10,
                            MONTH=10,
                            WEEK=10,
                            YEAR=10,
                            PROGRAM_DURATION=10,
                        ),
                    )
                ),
                [
                    DispatchOptOut(
                        timeperiod="DAY",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="WEEK",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="MONTH",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="YEAR",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="PROGRAM_DURATION",
                        value=10,
                    ),
                ],
                DemandManagementConstraints(
                    max_total_energy_per_timeperiod=10 * 60,
                    timeperiod=ProgramTimePeriod.WEEK,
                ),
                None,
                {
                    "id": 1,
                    "contract_id": 1,
                    "day": date(2023, 2, 24),
                    "cumulative_event_duration_day": 23 * 60,
                    "cumulative_event_duration_day_warning": True,
                    "cumulative_event_duration_day_violation": False,
                    "cumulative_event_duration_week": 100 * 60,
                    "cumulative_event_duration_week_warning": False,
                    "cumulative_event_duration_week_violation": False,
                    "cumulative_event_duration_month": 100 * 60,
                    "cumulative_event_duration_month_warning": False,
                    "cumulative_event_duration_month_violation": False,
                    "cumulative_event_duration_year": 100 * 60,
                    "cumulative_event_duration_year_warning": False,
                    "cumulative_event_duration_year_violation": False,
                    "cumulative_event_duration_program_duration": 100 * 60,
                    "cumulative_event_duration_program_duration_warning": True,
                    "cumulative_event_duration_program_duration_violation": True,
                    "max_number_of_events_per_timeperiod_day": 23,
                    "max_number_of_events_per_timeperiod_day_warning": True,
                    "max_number_of_events_per_timeperiod_day_violation": True,
                    "max_number_of_events_per_timeperiod_week": 100,
                    "max_number_of_events_per_timeperiod_week_warning": True,
                    "max_number_of_events_per_timeperiod_week_violation": True,
                    "max_number_of_events_per_timeperiod_month": 100,
                    "max_number_of_events_per_timeperiod_month_warning": True,
                    "max_number_of_events_per_timeperiod_month_violation": True,
                    "max_number_of_events_per_timeperiod_year": 100,
                    "max_number_of_events_per_timeperiod_year_warning": True,
                    "max_number_of_events_per_timeperiod_year_violation": True,
                    "max_number_of_events_per_timeperiod_program_duration": 100,
                    "max_number_of_events_per_timeperiod_program_duration_warning": True,
                    "max_number_of_events_per_timeperiod_program_duration_violation": True,
                    "opt_outs_day": 0,
                    "opt_outs_day_warning": False,
                    "opt_outs_day_violation": False,
                    "opt_outs_week": 0,
                    "opt_outs_week_warning": False,
                    "opt_outs_week_violation": False,
                    "opt_outs_month": 0,
                    "opt_outs_month_warning": False,
                    "opt_outs_month_violation": False,
                    "opt_outs_year": 0,
                    "opt_outs_year_warning": False,
                    "opt_outs_year_violation": False,
                    "opt_outs_program_duration": 0,
                    "opt_outs_program_duration_warning": False,
                    "opt_outs_program_duration_violation": False,
                    "max_total_energy_per_timeperiod_day": None,
                    "max_total_energy_per_timeperiod_day_warning": None,
                    "max_total_energy_per_timeperiod_day_violation": None,
                    "max_total_energy_per_timeperiod_week": Decimal("100.0000") * 60,
                    "max_total_energy_per_timeperiod_week_warning": True,
                    "max_total_energy_per_timeperiod_week_violation": True,
                    "max_total_energy_per_timeperiod_month": None,
                    "max_total_energy_per_timeperiod_month_warning": None,
                    "max_total_energy_per_timeperiod_month_violation": None,
                    "max_total_energy_per_timeperiod_year": None,
                    "max_total_energy_per_timeperiod_year_warning": None,
                    "max_total_energy_per_timeperiod_year_violation": None,
                    "max_total_energy_per_timeperiod_program_duration": None,
                    "max_total_energy_per_timeperiod_program_duration_warning": None,
                    "max_total_energy_per_timeperiod_program_duration_violation": None,
                },
                id="positive-constraints",
            ),
            pytest.param(
                Constraints.from_dict(
                    dict(
                        event_duration_constraint=dict(
                            min=1,
                            max=2,
                        ),
                        cumulative_event_duration=dict(
                            DAY=dict(
                                min=1 * 60,
                                max=24 * 60,
                            ),
                            WEEK=dict(
                                min=5 * 60,
                                max=140 * 60,
                            ),
                            MONTH=dict(
                                min=10 * 60,
                                max=1000 * 60,
                            ),
                            YEAR=dict(
                                min=10 * 60,
                                max=1200 * 60,
                            ),
                            PROGRAM_DURATION=dict(
                                min=1000 * 60,
                                max=1200 * 60,
                            ),
                        ),
                        max_number_of_events_per_timeperiod=dict(
                            DAY=10,
                            MONTH=10,
                            WEEK=10,
                            YEAR=10,
                            PROGRAM_DURATION=10,
                        ),
                    )
                ),
                [
                    DispatchOptOut(
                        timeperiod="DAY",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="WEEK",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="MONTH",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="YEAR",
                        value=10,
                    ),
                    DispatchOptOut(
                        timeperiod="PROGRAM_DURATION",
                        value=10,
                    ),
                ],
                DemandManagementConstraints(
                    max_total_energy_per_timeperiod=10 * 60,
                    timeperiod=ProgramTimePeriod.WEEK,
                ),
                2,
                {
                    "id": 1,
                    "contract_id": 1,
                    "day": date(2023, 2, 24),
                    "cumulative_event_duration_day": 12 * 60,
                    "cumulative_event_duration_day_warning": False,
                    "cumulative_event_duration_day_violation": False,
                    "cumulative_event_duration_week": 50 * 60,
                    "cumulative_event_duration_week_warning": False,
                    "cumulative_event_duration_week_violation": False,
                    "cumulative_event_duration_month": 50 * 60,
                    "cumulative_event_duration_month_warning": False,
                    "cumulative_event_duration_month_violation": False,
                    "cumulative_event_duration_year": 50 * 60,
                    "cumulative_event_duration_year_warning": False,
                    "cumulative_event_duration_year_violation": False,
                    "cumulative_event_duration_program_duration": 50 * 60,
                    "cumulative_event_duration_program_duration_warning": True,
                    "cumulative_event_duration_program_duration_violation": True,
                    "max_number_of_events_per_timeperiod_day": 12,
                    "max_number_of_events_per_timeperiod_day_warning": True,
                    "max_number_of_events_per_timeperiod_day_violation": True,
                    "max_number_of_events_per_timeperiod_week": 50,
                    "max_number_of_events_per_timeperiod_week_warning": True,
                    "max_number_of_events_per_timeperiod_week_violation": True,
                    "max_number_of_events_per_timeperiod_month": 50,
                    "max_number_of_events_per_timeperiod_month_warning": True,
                    "max_number_of_events_per_timeperiod_month_violation": True,
                    "max_number_of_events_per_timeperiod_year": 50,
                    "max_number_of_events_per_timeperiod_year_warning": True,
                    "max_number_of_events_per_timeperiod_year_violation": True,
                    "max_number_of_events_per_timeperiod_program_duration": 50,
                    "max_number_of_events_per_timeperiod_program_duration_warning": True,
                    "max_number_of_events_per_timeperiod_program_duration_violation": True,
                    "opt_outs_day": 11,
                    "opt_outs_day_warning": True,
                    "opt_outs_day_violation": True,
                    "opt_outs_week": 50,
                    "opt_outs_week_warning": True,
                    "opt_outs_week_violation": True,
                    "opt_outs_month": 50,
                    "opt_outs_month_warning": True,
                    "opt_outs_month_violation": True,
                    "opt_outs_year": 50,
                    "opt_outs_year_warning": True,
                    "opt_outs_year_violation": True,
                    "opt_outs_program_duration": 50,
                    "opt_outs_program_duration_warning": True,
                    "opt_outs_program_duration_violation": True,
                    "max_total_energy_per_timeperiod_day": None,
                    "max_total_energy_per_timeperiod_day_warning": None,
                    "max_total_energy_per_timeperiod_day_violation": None,
                    "max_total_energy_per_timeperiod_week": Decimal("50.0000") * 60,
                    "max_total_energy_per_timeperiod_week_warning": True,
                    "max_total_energy_per_timeperiod_week_violation": True,
                    "max_total_energy_per_timeperiod_month": None,
                    "max_total_energy_per_timeperiod_month_warning": None,
                    "max_total_energy_per_timeperiod_month_violation": None,
                    "max_total_energy_per_timeperiod_year": None,
                    "max_total_energy_per_timeperiod_year_warning": None,
                    "max_total_energy_per_timeperiod_year_violation": None,
                    "max_total_energy_per_timeperiod_program_duration": None,
                    "max_total_energy_per_timeperiod_program_duration_warning": None,
                    "max_total_energy_per_timeperiod_program_duration_violation": None,
                },
                id="every-second-event-negative",
            ),
            pytest.param(
                None,
                [],
                None,
                2,
                {
                    "id": 1,
                    "contract_id": 1,
                    "day": date(2023, 2, 24),
                    "cumulative_event_duration_day": None,
                    "cumulative_event_duration_day_warning": None,
                    "cumulative_event_duration_day_violation": None,
                    "cumulative_event_duration_week": None,
                    "cumulative_event_duration_week_warning": None,
                    "cumulative_event_duration_week_violation": None,
                    "cumulative_event_duration_month": None,
                    "cumulative_event_duration_month_warning": None,
                    "cumulative_event_duration_month_violation": None,
                    "cumulative_event_duration_year": None,
                    "cumulative_event_duration_year_warning": None,
                    "cumulative_event_duration_year_violation": None,
                    "cumulative_event_duration_program_duration": None,
                    "cumulative_event_duration_program_duration_warning": None,
                    "cumulative_event_duration_program_duration_violation": None,
                    "max_number_of_events_per_timeperiod_day": None,
                    "max_number_of_events_per_timeperiod_day_warning": None,
                    "max_number_of_events_per_timeperiod_day_violation": None,
                    "max_number_of_events_per_timeperiod_week": None,
                    "max_number_of_events_per_timeperiod_week_warning": None,
                    "max_number_of_events_per_timeperiod_week_violation": None,
                    "max_number_of_events_per_timeperiod_month": None,
                    "max_number_of_events_per_timeperiod_month_warning": None,
                    "max_number_of_events_per_timeperiod_month_violation": None,
                    "max_number_of_events_per_timeperiod_year": None,
                    "max_number_of_events_per_timeperiod_year_warning": None,
                    "max_number_of_events_per_timeperiod_year_violation": None,
                    "max_number_of_events_per_timeperiod_program_duration": None,
                    "max_number_of_events_per_timeperiod_program_duration_warning": None,
                    "max_number_of_events_per_timeperiod_program_duration_violation": None,
                    "opt_outs_day": None,
                    "opt_outs_day_warning": None,
                    "opt_outs_day_violation": None,
                    "opt_outs_week": None,
                    "opt_outs_week_warning": None,
                    "opt_outs_week_violation": None,
                    "opt_outs_month": None,
                    "opt_outs_month_warning": None,
                    "opt_outs_month_violation": None,
                    "opt_outs_year": None,
                    "opt_outs_year_warning": None,
                    "opt_outs_year_violation": None,
                    "opt_outs_program_duration": None,
                    "opt_outs_program_duration_warning": None,
                    "opt_outs_program_duration_violation": None,
                    "max_total_energy_per_timeperiod_day": None,
                    "max_total_energy_per_timeperiod_day_warning": None,
                    "max_total_energy_per_timeperiod_day_violation": None,
                    "max_total_energy_per_timeperiod_week": None,
                    "max_total_energy_per_timeperiod_week_warning": None,
                    "max_total_energy_per_timeperiod_week_violation": None,
                    "max_total_energy_per_timeperiod_month": None,
                    "max_total_energy_per_timeperiod_month_warning": None,
                    "max_total_energy_per_timeperiod_month_violation": None,
                    "max_total_energy_per_timeperiod_year": None,
                    "max_total_energy_per_timeperiod_year_warning": None,
                    "max_total_energy_per_timeperiod_year_violation": None,
                    "max_total_energy_per_timeperiod_program_duration": None,
                    "max_total_energy_per_timeperiod_program_duration_warning": None,
                    "max_total_energy_per_timeperiod_program_duration_violation": None,
                },
                id="no-constraints",
            ),
        ],
    )
    def test_calculate_constraints(
        self,
        dispatch_constraints,
        dispatch_opt_outs,
        demand_management_constraints,
        negative_on,
        expected_result,
        db_session,
    ):
        now = pendulum.now().utcnow()
        with mock.patch("pendulum.now", return_value=now):
            number_of_events = 100
            program = factories.ProgramFactory(
                start_date=pendulum.now().subtract(hours=2000),
                dispatch_constraints=dispatch_constraints,
                dispatch_max_opt_outs=dispatch_opt_outs,
                demand_management_constraints=demand_management_constraints,
            )
            day = self._create_events(db_session, number_of_events, program, negative_on)
            EventController().calculate_contract_constraints(day)
            summary = self._get_all(db_session, ContractConstraintSummary)

            assert len(summary) == 1
            summary_dict = summary[0].to_dict()
            summary_dict.pop("created_at")
            summary_dict.pop("updated_at")
            assert summary_dict == expected_result
