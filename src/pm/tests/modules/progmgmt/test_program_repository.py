from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from pm.modules.progmgmt.enums import (
    AvailabilityType,
    DOECalculationFrequency,
    DOELimitType,
    OrderType,
    ProgramCategory,
    ProgramOrderBy,
    ProgramStatus,
    ProgramTimePeriod,
    ScheduleTimeperiod,
)
from pm.modules.progmgmt.models.avail_operating_months import AvailOperatingMonths
from pm.modules.progmgmt.models.avail_service_window import AvailServiceWindow
from pm.modules.progmgmt.models.dispatch_notification import DispatchNotification
from pm.modules.progmgmt.models.dispatch_opt_out import DispatchOptOut
from pm.modules.progmgmt.models.program import (
    Constraints,
    DynamicOperatingEnvelopesProgram,
    Program,
    ResourceEligibilityCriteria,
)
from pm.modules.progmgmt.repository import ProgramRepository
from pm.tests import factories
from shared.enums import DOEControlType, ProgramPriority, ProgramTypeEnum


@pytest.fixture
def fake_program():
    return Program(
        name="name",
        program_type=ProgramTypeEnum.GENERIC,
        program_category=ProgramCategory.LIMIT_BASED,
        status=ProgramStatus.ACTIVE,
        start_date=datetime(2022, 9, 1),
        end_date=datetime(2023, 9, 1),
        program_priority=ProgramPriority.P0,
        availability_type=AvailabilityType.SERVICE_WINDOWS,
        check_der_eligibility=True,
        define_contractual_target_capacity=True,
        dispatch_constraints=Constraints.from_dict(
            dict(
                event_duration_constraint=dict(
                    min=1,
                    max=2,
                )
            )
        ),
        resource_eligibility_criteria=ResourceEligibilityCriteria(
            max_real_power_rating=10.0,
            min_real_power_rating=2.0,
        ),
        notification_type="SMS_EMAIL",
        avail_operating_months=AvailOperatingMonths(
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
        dispatch_max_opt_outs=[
            DispatchOptOut(
                timeperiod=ProgramTimePeriod.DAY,
                value=10,
            )
        ],
        dispatch_notifications=[DispatchNotification(text="test", lead_time=10)],
        avail_service_windows=[
            AvailServiceWindow(
                start_hour=1,
                end_hour=10,
                mon=True,
                tue=True,
                wed=True,
                thu=True,
                fri=True,
                sat=True,
                sun=True,
            )
        ],
    )


@pytest.fixture
def program_list():
    p1 = factories.ProgramFactory(
        name="1",
        program_type=ProgramTypeEnum.GENERIC,
        program_category=ProgramCategory.LIMIT_BASED,
        availability_type=AvailabilityType.ALWAYS_AVAILABLE,
        status=ProgramStatus.ARCHIVED,
        avail_operating_months=AvailOperatingMonths(
            jan=True,
            feb=True,
            mar=True,
            apr=True,
            may=True,
            jun=True,
            jul=True,
            aug=True,
            sep=True,
            oct=True,
            nov=True,
            dec=True,
        ),
        start_date=datetime(2022, 12, 7),
        end_date=None,
        created_at=datetime(2022, 12, 2, tzinfo=timezone.utc),
        program_priority=ProgramPriority.P0,
        check_der_eligibility=True,
    )
    p2 = factories.ProgramFactory(
        name="2",
        program_type=ProgramTypeEnum.GENERIC,
        program_category=ProgramCategory.GENERIC,
        availability_type=AvailabilityType.ALWAYS_AVAILABLE,
        status=ProgramStatus.PUBLISHED,
        avail_operating_months=AvailOperatingMonths(
            jan=True,
            feb=True,
            mar=True,
            apr=True,
            may=True,
            jun=True,
            jul=True,
            aug=True,
            sep=True,
            oct=True,
            nov=True,
            dec=True,
        ),
        start_date=datetime(2022, 12, 12),
        end_date=datetime(2023, 7, 15),
        created_at=datetime(2022, 6, 8, tzinfo=timezone.utc),
        program_priority=ProgramPriority.P0,
        check_der_eligibility=True,
    )
    p3 = factories.ProgramFactory(
        name="3",
        program_type=ProgramTypeEnum.GENERIC,
        program_category=ProgramCategory.LIMIT_BASED,
        availability_type=AvailabilityType.ALWAYS_AVAILABLE,
        status=ProgramStatus.PUBLISHED,
        avail_operating_months=AvailOperatingMonths(
            jan=True,
            feb=True,
            mar=True,
            apr=True,
            may=True,
            jun=True,
            jul=True,
            aug=True,
            sep=True,
            oct=True,
            nov=True,
            dec=True,
        ),
        start_date=datetime(2022, 12, 8),
        end_date=datetime(2024, 12, 15),
        created_at=datetime(2022, 12, 8, tzinfo=timezone.utc),
        program_priority=ProgramPriority.P0,
        check_der_eligibility=True,
    )
    p4 = factories.ProgramFactory(
        name="4",
        program_type=ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
        program_category=ProgramCategory.LIMIT_BASED,
        availability_type=AvailabilityType.ALWAYS_AVAILABLE,
        status=ProgramStatus.DRAFT,
        avail_operating_months=AvailOperatingMonths(
            jan=True,
            feb=True,
            mar=True,
            apr=True,
            may=True,
            jun=True,
            jul=True,
            aug=True,
            sep=True,
            oct=True,
            nov=True,
            dec=True,
        ),
        start_date=datetime(2022, 12, 30),
        end_date=datetime(2025, 11, 1),
        created_at=datetime(2023, 11, 8, tzinfo=timezone.utc),
        program_priority=ProgramPriority.P0,
        check_der_eligibility=True,
    )
    p5 = factories.ProgramFactory(
        name="5",
        program_type=ProgramTypeEnum.DEMAND_MANAGEMENT,
        program_category=ProgramCategory.TARGET_BASED,
        availability_type=AvailabilityType.ALWAYS_AVAILABLE,
        status=ProgramStatus.ACTIVE,
        avail_operating_months=AvailOperatingMonths(
            jan=True,
            feb=True,
            mar=True,
            apr=True,
            may=True,
            jun=True,
            jul=True,
            aug=True,
            sep=True,
            oct=True,
            nov=True,
            dec=True,
        ),
        start_date=datetime(2022, 12, 14),
        end_date=datetime(2023, 5, 1),
        created_at=datetime(2022, 3, 8, tzinfo=timezone.utc),
        program_priority=ProgramPriority.P0,
        check_der_eligibility=True,
    )
    p6 = factories.ProgramFactory(
        name="6",
        program_type=ProgramTypeEnum.GENERIC,
        program_category=ProgramCategory.LIMIT_BASED,
        availability_type=AvailabilityType.ALWAYS_AVAILABLE,
        status=ProgramStatus.PUBLISHED,
        avail_operating_months=AvailOperatingMonths(
            jan=True,
            feb=True,
            mar=True,
            apr=True,
            may=True,
            jun=True,
            jul=True,
            aug=True,
            sep=True,
            oct=True,
            nov=True,
            dec=True,
        ),
        start_date=datetime(2022, 11, 8),
        end_date=datetime(2023, 11, 1),
        created_at=datetime(2022, 12, 20, tzinfo=timezone.utc),
        program_priority=ProgramPriority.P0,
        check_der_eligibility=True,
    )

    return [p1, p2, p3, p4, p5, p6]


class TestProgramRepository:
    def test_save(self, db_session, fake_program):
        with db_session() as session:
            program_id = 1
            repo = ProgramRepository(session)
            program = repo.get(program_id)
            assert program is None
            repo.save(fake_program)
            program = repo.get(program_id)
            assert program is not None

    def test_save_relationships(self, db_session, fake_program):
        program_id = 1
        with db_session() as session:
            repo = ProgramRepository(session)
            repo.save(fake_program)
            session.commit()
            program = repo.get(program_id)
            session.commit()
            repo.save(program)
            session.commit()
            program = repo.get(program_id)
            assert len(program.avail_service_windows) == 1
            windows = session.execute(select(AvailServiceWindow)).scalars().all()
            assert len(windows) == 1

    def test_count_program(self, db_session):
        with db_session() as session:
            program_name = "name"
            repo = ProgramRepository(session)
            count = repo.count_by_name(program_name)
            assert count == 0
            factories.ProgramFactory(name=program_name)
            count = repo.count_by_name("name")
            assert count == 1

    def test_get_paginated_list(self, db_session, program_list):
        with db_session() as session:
            expected = len(program_list)
            result = ProgramRepository(session).get_paginated_list(
                pagination_start=1, pagination_end=1000
            )
            assert len(result.results) == expected
            assert result.count == expected

    @pytest.mark.parametrize(
        "status,program_type,expected",
        [
            pytest.param(ProgramStatus.ACTIVE, None, 1),
            pytest.param(None, ProgramTypeEnum.DEMAND_MANAGEMENT, 1),
            pytest.param(ProgramStatus.PUBLISHED, ProgramTypeEnum.GENERIC, 3),
        ],
    )
    def test_get_paginated_list_filter_status_program_type(
        self, db_session, program_list, status, program_type, expected
    ):
        with db_session() as session:
            result = ProgramRepository(session).get_paginated_list(
                status=status,
                program_type=program_type,
                pagination_start=1,
                pagination_end=1000,
            )
            assert len(result.results) == expected
            assert result.count == expected
            for p in result.results:
                if status is not None:
                    assert p.status == status
                if program_type is not None:
                    assert p.program_type == program_type

    @pytest.mark.parametrize(
        "start_date,end_date,expected",
        [
            pytest.param(datetime(2022, 12, 8, tzinfo=timezone.utc), None, 4),
            pytest.param(None, datetime(2024, 12, 14, tzinfo=timezone.utc), 3),
            pytest.param(
                datetime(2022, 12, 9, tzinfo=timezone.utc),
                datetime(2024, 12, 15, tzinfo=timezone.utc),
                2,
            ),
        ],
    )
    def test_get_paginated_list_filter_by_date(
        self, db_session, program_list, start_date, end_date, expected
    ):
        with db_session() as session:
            result = ProgramRepository(session).get_paginated_list(
                start_date=start_date, end_date=end_date, pagination_start=1, pagination_end=1000
            )
            assert len(result.results) == expected
            assert result.count == expected
            for p in result.results:
                if start_date is not None:
                    assert p.start_date >= start_date
                if end_date is not None:
                    assert p.end_date <= end_date

    @pytest.mark.parametrize(
        "order_by,order_type,expected_names_order",
        [
            pytest.param(ProgramOrderBy.CREATED_AT, OrderType.ASC, ["5", "2", "1", "3", "6", "4"]),
            pytest.param(ProgramOrderBy.NAME, OrderType.DESC, ["6", "5", "4", "3", "2", "1"]),
            pytest.param(
                ProgramOrderBy.PROGRAM_TYPE, OrderType.ASC, ["5", "4", "1", "2", "3", "6"]
            ),
            pytest.param(ProgramOrderBy.START_DATE, OrderType.DESC, ["4", "5", "2", "3", "1", "6"]),
            pytest.param(ProgramOrderBy.END_DATE, None, ["5", "2", "6", "3", "4", "1"]),
            pytest.param(None, None, ["4", "5", "6", "3", "2", "1"]),
        ],
    )
    def test_get_paginated_list_with_sort_options(
        self, db_session, program_list, order_by, order_type, expected_names_order
    ):
        with db_session() as session:
            result = ProgramRepository(session).get_paginated_list(
                order_by=order_by, order_type=order_type, pagination_start=1, pagination_end=1000
            )
            assert len(result.results) == 6
            assert result.count == 6

            assert [p.name for p in result.results] == expected_names_order

    def test_get_paginated_list_with_pagination(self, db_session, program_list):
        expected_names_order = ["4", "5", "6", "3", "2", "1"]
        with db_session() as session:
            repo = ProgramRepository(session)
            first_result = repo.get_paginated_list(pagination_start=1, pagination_end=1)
            assert len(first_result.results) == 1
            assert first_result.count == 6

            second_result = repo.get_paginated_list(pagination_start=2, pagination_end=3)
            assert len(second_result.results) == 2
            assert second_result.count == 6

            third_result = repo.get_paginated_list(pagination_start=4, pagination_end=1000)
            assert len(third_result.results) == 3
            assert third_result.count == 6

            results = first_result.results + second_result.results + third_result.results

            assert [p.name for p in results] == expected_names_order

    def test_dynamic_operating_envelopes_save(self, db_session):
        with db_session() as session:
            program = DynamicOperatingEnvelopesProgram(
                name="test",
                program_type=ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                limit_type=DOELimitType.REAL_POWER,
                control_type=[DOEControlType.CONNECTION_POINT_EXPORT_LIMIT],
                calculation_frequency=DOECalculationFrequency.DAILY,
                schedule_time_horizon_timeperiod=ScheduleTimeperiod.DAYS,
                schedule_time_horizon_number=4,
                schedule_timestep_mins=10,
            )
            ProgramRepository(session).save(program)
            session.commit()
            p = session.query(Program).get(1)
            assert p.limit_type == DOELimitType.REAL_POWER
            assert p.control_type == [DOEControlType.CONNECTION_POINT_EXPORT_LIMIT]
            assert p.calculation_frequency == DOECalculationFrequency.DAILY
            assert p.schedule_time_horizon_timeperiod == ScheduleTimeperiod.DAYS
            assert p.schedule_time_horizon_number == 4
            assert p.schedule_timestep_mins == 10

    def test_get_no_eager_load(self, db_session):
        program = factories.ProgramFactory()
        with db_session() as session:
            got = ProgramRepository(session).get(program.id, eager_load_relationships=False)
            assert got is not None
