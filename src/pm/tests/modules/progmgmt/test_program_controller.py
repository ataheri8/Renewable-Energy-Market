import pathlib
from datetime import datetime, timezone
from typing import Optional

import pendulum
import pytest
from sqlalchemy.orm import Session as S

from pm.modules.enrollment.enums import ContractStatus
from pm.modules.progmgmt.controller import InvalidProgramArgs, ProgramController
from pm.modules.progmgmt.enums import (
    AvailabilityType,
    EnergyUnit,
    NotificationType,
    ProgramCategory,
    ProgramStatus,
    ProgramTimePeriod,
)
from pm.modules.progmgmt.models.avail_operating_months import AvailOperatingMonths
from pm.modules.progmgmt.models.avail_service_window import AvailServiceWindow
from pm.modules.progmgmt.models.dispatch_opt_out import DispatchOptOut
from pm.modules.progmgmt.models.program import (
    Constraints,
    CreateUpdateProgram,
    DemandManagementConstraints,
    InvalidProgramStatus,
    Program,
    ResourceEligibilityCriteria,
)
from pm.modules.progmgmt.repository import ProgramNotDraft
from pm.tests import factories
from shared.enums import ProgramPriority, ProgramTypeEnum
from shared.repository import PaginatedQuery
from shared.system import configuration
from shared.system.database import Session


class TestProgramController:
    def _get_all_programs(self) -> list[Program]:
        s: S
        with Session() as s:
            return s.query(Program).all()

    def _get_one_program(self, prog_id: int) -> Optional[Program]:
        s: S
        with Session() as s:
            return s.query(Program).get(prog_id)

    def _get_test_data_path(self, filename: str):
        path = str(pathlib.Path(__file__).parent.parent)
        return path + "/test_data/" + filename

    @pytest.mark.parametrize(
        "program_args",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        name="name",
                        program_type=ProgramTypeEnum.GENERIC,
                        program_category=ProgramCategory.LIMIT_BASED,
                        start_date=datetime(2022, 9, 1),
                        end_date=datetime(2023, 9, 1),
                        program_priority=ProgramPriority.P0,
                        availability_type=AvailabilityType.SERVICE_WINDOWS,
                        check_der_eligibility=True,
                        status=ProgramStatus.PUBLISHED,
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
                        )
                    ),
                    resource_eligibility_criteria=dict(
                        max_real_power_rating=10.0,
                        min_real_power_rating=2.0,
                    ),
                    dispatch_max_opt_outs=[
                        dict(
                            timeperiod=ProgramTimePeriod.DAY,
                            value=10,
                        )
                    ],
                    dispatch_notifications=[dict(text="my notification", lead_time=10)],
                    define_contractual_target_capacity=True,
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
                        )
                    ],
                ),
                id="all-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        name="name",
                        program_type=ProgramTypeEnum.GENERIC,
                    ),
                ),
                id="minimum-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        name="name",
                        program_type=ProgramTypeEnum.GENERIC,
                        status=ProgramStatus.DRAFT,
                    ),
                ),
                id="create-as-draft",
            ),
        ],
    )
    def test_create_program(self, program_args, db_session):
        data = CreateUpdateProgram.from_dict(program_args)
        ProgramController().create_program(data)
        programs = self._get_all_programs()
        assert len(programs) == 1

    @pytest.mark.parametrize(
        "initial_status,set_status",
        [
            pytest.param(ProgramStatus.DRAFT, ProgramStatus.PUBLISHED, id="draft-to-published"),
            pytest.param(
                ProgramStatus.PUBLISHED, ProgramStatus.ARCHIVED, id="published-to-archived"
            ),
            pytest.param(ProgramStatus.DRAFT, ProgramStatus.ARCHIVED, id="draft-to-archived"),
        ],
    )
    def test_update_program_status(self, db_session, initial_status, set_status):
        program_id = 1
        factories.ProgramFactory(id=program_id, status=initial_status)
        data = CreateUpdateProgram.from_dict({"general_fields": {"status": set_status}})
        ProgramController().save_program(program_id, data)
        program = self._get_one_program(program_id)
        assert program.status == set_status

    @pytest.mark.parametrize(
        "initial_status,set_status",
        [
            pytest.param(ProgramStatus.PUBLISHED, ProgramStatus.DRAFT, id="published-to-draft"),
            pytest.param(ProgramStatus.DRAFT, ProgramStatus.ACTIVE, id="draft-to-active"),
        ],
    )
    def test_update_program_status_fail(self, db_session, initial_status, set_status):
        program_id = 1
        factories.ProgramFactory(id=program_id, status=initial_status)
        data = CreateUpdateProgram.from_dict({"general_fields": {"status": set_status}})
        with pytest.raises(InvalidProgramStatus):
            ProgramController().save_program(program_id, data)
            program = self._get_one_program(program_id)
            assert program.status == set_status

    def test_create_with_demand_managment_dispatch_constrains(self, db_session):
        program_args = dict(
            general_fields=dict(
                name="name",
                program_type=ProgramTypeEnum.DEMAND_MANAGEMENT,
            ),
            demand_management_constraints=dict(
                max_total_energy_per_timeperiod=20,
                max_total_energy_unit=EnergyUnit.KWH,
                timeperiod=ProgramTimePeriod.DAY,
            ),
        )
        data: CreateUpdateProgram = CreateUpdateProgram.from_dict(program_args)
        ProgramController().create_program(data)
        programs = self._get_all_programs()
        assert len(programs) == 1
        assert programs[0].demand_management_constraints.max_total_energy_unit == EnergyUnit.KWH

    def test_create_program_error(self):
        with pytest.raises(InvalidProgramArgs):
            data = CreateUpdateProgram.from_dict({"general_fields": {}})
            ProgramController().create_program(data)

    @pytest.mark.parametrize(
        "program_args",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_category=ProgramCategory.LIMIT_BASED,
                        start_date=datetime(2022, 9, 1),
                        end_date=datetime(2023, 9, 1),
                        program_priority=ProgramPriority.P0,
                        availability_type=AvailabilityType.SERVICE_WINDOWS,
                        check_der_eligibility=True,
                        notification_type=NotificationType.SMS_EMAIL,
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
                        )
                    ),
                    resource_eligibility_criteria=dict(
                        max_real_power_rating=10.0,
                        min_real_power_rating=2.0,
                    ),
                    dispatch_max_opt_outs=[
                        dict(
                            timeperiod=ProgramTimePeriod.DAY,
                            value=10,
                        )
                    ],
                    dispatch_notifications=[dict(text="my notification", lead_time=10)],
                    define_contractual_target_capacity=True,
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
                        )
                    ],
                ),
                id="all-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(name="newname"),
                ),
                id="minimum-fields",
            ),
        ],
    )
    def test_save_program(self, db_session, program_args):
        program = factories.DemandManagementProgramFactory()
        program_id = program.id
        program_name = program.name
        data = CreateUpdateProgram.from_dict(program_args)
        ProgramController().save_program(program_id, data)
        changed_program = self._get_one_program(program_id)
        expected_name = program_args["general_fields"].get("name", program_name)

        programs = self._get_all_programs()
        assert len(programs) == 1
        assert changed_program.name == expected_name

    def test_save_holiday_exclusion(self, db_session):
        program = factories.ProgramFactory()
        program_id = program.id
        holiday_args = (
            {
                "calendars": [
                    {
                        "mrid": "system",
                        "timezone": "Europe/Paris",
                        "year": 2021,
                        "events": [
                            {
                                "startDate": "2021-01-01",
                                "endDate": "2021-01-01",
                                "name": "New year",
                                "category": "holiday",
                                "substitutionDate": "2020-01-01",
                            },
                            {
                                "startDate": "2021-04-02",
                                "endDate": "2021-04-02",
                                "name": "Easter Monday",
                                "category": "holiday",
                                "substitutionDate": "2021-05-01",
                            },
                            {
                                "startDate": "2021-05-01",
                                "endDate": "2021-05-01",
                                "name": "Labour Day",
                                "category": "holiday",
                            },
                        ],
                    }
                ]
            },
        )
        ProgramController().save_holiday_exclusion(program_id, holiday_args)
        programs = self._get_all_programs()
        assert len(programs) == 1

    def test_archive_program(self, db_session):
        program = factories.ProgramFactory()
        program_id = program.id
        ProgramController().archive_program(program_id)
        program = self._get_one_program(program_id)
        assert program.status == ProgramStatus.ARCHIVED

    def test_expire_contract_for_archive_program(self, db_session):
        program = factories.ProgramFactory()
        program_id = program.id
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der1,
        )
        contract = factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
        )
        assert contract.contract_status != ContractStatus.EXPIRED
        ProgramController().archive_program(program_id)
        ProgramController().expire_contract_for_archive_program(program_id)
        # with db_session() as session:
        #     contract = ContractRepository(session).get(contract_id=contract.id,eager_load=True)
        # assert contract.contract_status == ContractStatus.EXPIRED

    def test_archive_program_error(self, db_session):
        with pytest.raises(InvalidProgramStatus):
            program = factories.ProgramFactory(id=1, status=ProgramStatus.ARCHIVED)
            ProgramController().archive_program(program.id)

    def test_get_empty_program_list(self, db_session):
        config = configuration.get_config()
        got = ProgramController().get_program_list(
            {
                "pagination_start": 1,
                "pagination_end": config.PAGINATION_DEFAULT_LIMIT,
            }
        )
        expected = PaginatedQuery(
            pagination_start=1,
            pagination_end=config.PAGINATION_DEFAULT_LIMIT,
            count=0,
            results=[],
        )
        assert got == expected

    def test_get_program_list(self, db_session):
        p1_args = dict(
            name="test program",
            program_type=ProgramTypeEnum.GENERIC,
            program_category=ProgramCategory.LIMIT_BASED,
            availability_type=AvailabilityType.ALWAYS_AVAILABLE,
            status=ProgramStatus.ACTIVE,
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
            start_date=datetime(2022, 11, 8, tzinfo=timezone.utc),
            end_date=datetime(2023, 11, 1, tzinfo=timezone.utc),
            program_priority=ProgramPriority.P0,
            check_der_eligibility=True,
            dispatch_constraints=Constraints(),
            resource_eligibility_criteria=ResourceEligibilityCriteria(),
        )
        p2_args = dict(
            name="not finished program",
            program_type=ProgramTypeEnum.DEMAND_MANAGEMENT,
            program_category=ProgramCategory.TARGET_BASED,
            availability_type=AvailabilityType.SERVICE_WINDOWS,
            status=ProgramStatus.DRAFT,
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
            program_priority=ProgramPriority.P0,
            check_der_eligibility=True,
            dispatch_constraints=Constraints(),
            demand_management_constraints=DemandManagementConstraints(),
            resource_eligibility_criteria=ResourceEligibilityCriteria(),
        )

        factories.ProgramFactory(**p1_args)
        factories.ProgramFactory(**p2_args)

        result = ProgramController().get_program_list({"pagination_start": 1, "pagination_end": 2})
        assert len(result.results) == 2
        # p2_args are ordered by status
        for r, args in zip(result.results, [p2_args, p1_args]):
            assert r.name == args["name"]
            assert r.program_type == args["program_type"]
            assert r.availability_type == args["availability_type"]
            assert r.status == args["status"]
            assert r.created_at == args["created_at"]

        assert result.pagination_start == 1
        assert result.pagination_end == 2
        assert result.count == 2

    def test_get_holiday_exclusions(self, db_session):
        holiday_payload = {
            "calendars": [
                {
                    "mrid": "system",
                    "timezone": "Europe/Paris",
                    "year": 2021,
                    "events": [
                        {
                            "startDate": "2021-01-01",
                            "endDate": "2021-01-01",
                            "name": "New year",
                            "category": "holiday",
                            "substitutionDate": "2020-01-01",
                        },
                        {
                            "startDate": "2021-04-02",
                            "endDate": "2021-04-02",
                            "name": "Easter Monday",
                            "category": "holiday",
                            "substitutionDate": "2021-05-01",
                        },
                        {
                            "startDate": "2021-05-01",
                            "endDate": "2021-05-01",
                            "name": "Labour Day",
                            "category": "holiday",
                        },
                    ],
                }
            ]
        }
        program = factories.ProgramFactory(holiday_exclusions=holiday_payload)
        result = ProgramController().get_holiday_exclusions(program.id)

        assert len(result) == 3
        assert result == holiday_payload["calendars"][0]["events"]

    def test_get_holiday_exclusions_no_calendars(self, db_session):
        program = factories.ProgramFactory()
        result = ProgramController().get_holiday_exclusions(program.id)

        assert result == []

    def test_get_all_programs(self, db_session):
        factories.ProgramFactory()
        factories.ProgramFactory()
        got = ProgramController().get_all_programs()
        assert len(got) == 2

    def test_delete_program_error(self, db_session):
        program = factories.GenericProgramFactory(status=ProgramStatus.ACTIVE)
        program_id = program.id
        with pytest.raises(ProgramNotDraft):
            ProgramController().delete_draft_program(program_id)

    def test_delete_draft_program(self, db_session):
        program = factories.GenericProgramFactory(status=ProgramStatus.DRAFT)
        program_id = program.id
        ProgramController().delete_draft_program(program_id)
        program = self._get_one_program(program_id)
        assert program is None
        with db_session() as session:
            # assert all related tables are deleted
            assert session.query(Program).count() == 0
            assert session.query(AvailOperatingMonths).count() == 0
            assert session.query(AvailServiceWindow).count() == 0
            assert session.query(DispatchOptOut).count() == 0

    @pytest.mark.parametrize(
        "statuses,time,expected_active_count",
        [
            pytest.param(
                [
                    ProgramStatus.DRAFT,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ARCHIVED,
                    ProgramStatus.PUBLISHED,
                ],
                pendulum.now().subtract(days=1),
                2,
                id="should-publish-one-program-and-one-active",
            ),
            pytest.param(
                [
                    ProgramStatus.PUBLISHED,
                    ProgramStatus.PUBLISHED,
                    ProgramStatus.PUBLISHED,
                    ProgramStatus.PUBLISHED,
                ],
                pendulum.now().subtract(days=1),
                4,
                id="should-publish-all-programs",
            ),
            pytest.param(
                [
                    ProgramStatus.PUBLISHED,
                    ProgramStatus.PUBLISHED,
                    ProgramStatus.PUBLISHED,
                    ProgramStatus.PUBLISHED,
                ],
                pendulum.now().add(days=1),
                0,
                id="should-not-publish-any-programs",
            ),
        ],
    )
    def test_activate_programs(self, db_session, statuses, time, expected_active_count):
        for status in statuses:
            factories.GenericProgramFactory(status=status, start_date=time)
        ProgramController().activate_programs()
        with db_session() as session:
            got_active_count = (
                session.query(Program).filter(Program.status == ProgramStatus.ACTIVE).count()
            )
            assert got_active_count == expected_active_count

    @pytest.mark.parametrize(
        "statuses,time,expected_active_count",
        [
            pytest.param(
                [
                    ProgramStatus.DRAFT,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ARCHIVED,
                    ProgramStatus.PUBLISHED,
                ],
                pendulum.now().subtract(days=1),
                2,
                id="should-archive-one-program-and-one-archived",
            ),
            pytest.param(
                [
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ACTIVE,
                ],
                pendulum.now().subtract(days=1),
                4,
                id="should-archive-all-programs",
            ),
            pytest.param(
                [
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ACTIVE,
                ],
                pendulum.now().add(days=1),
                0,
                id="should-not-archive-any-programs",
            ),
        ],
    )
    def test_archive_programs(self, db_session, statuses, time, expected_active_count):
        for status in statuses:
            factories.GenericProgramFactory(status=status, end_date=time)
        ProgramController().archive_expired_programs()
        with db_session() as session:
            got_active_count = (
                session.query(Program).filter(Program.status == ProgramStatus.ARCHIVED).count()
            )
            assert got_active_count == expected_active_count
