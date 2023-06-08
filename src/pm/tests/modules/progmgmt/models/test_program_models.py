from datetime import datetime

import pendulum
import pytest

from pm.modules.progmgmt.enums import (
    AvailabilityType,
    DispatchLeadTimeEnum,
    DOECalculationFrequency,
    DOELimitType,
    ProgramCategory,
    ProgramStatus,
    ProgramTimePeriod,
    ScheduleTimeperiod,
)
from pm.modules.progmgmt.models.avail_operating_months import AvailOperatingMonths
from pm.modules.progmgmt.models.avail_service_window import (
    AvailServiceWindow,
    ServiceWindowOverlapViolation,
)
from pm.modules.progmgmt.models.dispatch_notification import DispatchNotification
from pm.modules.progmgmt.models.dispatch_opt_out import (
    DispatchOptOut,
    OptOutTimeperiodUniqueViolation,
)
from pm.modules.progmgmt.models.program import (
    Constraints,
    CreateUpdateProgram,
    DynamicOperatingEnvelopeFields,
    DynamicOperatingEnvelopesProgram,
    InvalidProgramStartEndTimes,
    Program,
    ProgramNameDuplicate,
    ProgramSaveViolation,
    ResourceEligibilityCriteria,
)
from shared.enums import (
    ControlOptionsEnum,
    DOEControlType,
    ProgramPriority,
    ProgramTypeEnum,
)


class TestProgramModels:
    @pytest.mark.parametrize("program_type", [*ProgramTypeEnum])
    def test_create_generic_program(self, program_type):
        program = Program.factory("name", program_type)
        assert program is not None

    @pytest.mark.parametrize("program_type", [*ProgramTypeEnum])
    def test_set_program_fields(self, program_type):
        name = "test"
        program_args = dict(
            general_fields=dict(
                program_category=ProgramCategory.LIMIT_BASED,
                start_date=datetime(2022, 9, 1),
                end_date=datetime(2023, 9, 1),
                program_priority=ProgramPriority.P0,
                availability_type=AvailabilityType.SERVICE_WINDOWS,
                check_der_eligibility=True,
                archived=False,
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
            dynamic_operating_envelope_fields=DynamicOperatingEnvelopeFields(
                limit_type=DOELimitType.REACTIVE_POWER.name,
                calculation_frequency=DOECalculationFrequency.DAILY.name,
                schedule_time_horizon_timeperiod=ScheduleTimeperiod.DAYS.name,
                schedule_time_horizon_number=1,
                schedule_timestep_mins=10,
            ),
            dispatch_max_opt_outs=[
                dict(
                    timeperiod=ProgramTimePeriod.DAY,
                    value=10,
                )
            ],
            dispatch_notifications=[dict(text="my notification", lead_time=10)],
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
        )
        program = Program.factory(name=name, program_type=program_type)
        data = CreateUpdateProgram.from_dict(program_args)
        program.set_program_fields(data)
        assert program.name == name
        if program_type == ProgramTypeEnum.GENERIC:
            assert isinstance(program.dispatch_constraints, Constraints)
        assert isinstance(program.resource_eligibility_criteria, ResourceEligibilityCriteria)
        assert isinstance(program.avail_operating_months, AvailOperatingMonths)
        assert isinstance(program.avail_service_windows[0], AvailServiceWindow)
        assert isinstance(program.dispatch_max_opt_outs[0], DispatchOptOut)
        assert isinstance(program.dispatch_notifications[0], DispatchNotification)

    def test_set_start_end_time(self):
        start = datetime(2022, 1, 10)
        end = datetime(2022, 10, 1)
        args = {
            "name": "test",
            "program_type": ProgramTypeEnum.GENERIC,
        }
        program = Program.factory(**args)
        program._set_start_end_time(start, end)
        assert program.start_date == start
        assert program.end_date == end

    @pytest.mark.parametrize(
        "start,end",
        [
            pytest.param(datetime(2022, 1, 10), datetime(2022, 1, 10), id="same-time"),
            pytest.param(datetime(2022, 7, 10), datetime(2022, 1, 10), id="start-after-end"),
            pytest.param(None, datetime(2021, 1, 10), id="no-start"),
            pytest.param(datetime(2022, 10, 10), None, id="no-end"),
        ],
    )
    def test_set_start_end_time_invalid(self, start, end):
        """Start time must be before end time"""
        with pytest.raises(InvalidProgramStartEndTimes):
            default_time = datetime(2022, 1, 1)
            start_time = start if start else default_time
            end_time = end if end else default_time
            args = {
                "name": "test",
                "program_type": ProgramTypeEnum.GENERIC,
            }
            program = Program.factory(**args)
            program._set_start_end_time(start_time, end_time)
            assert program.start_date == start
            assert program.end_date == end

    def test_set_name(self):
        args = {
            "name": "test",
            "program_type": ProgramTypeEnum.GENERIC,
        }
        program = Program.factory(**args)
        program.set_name("newname", 0)
        assert program.name == "newname"

    def test_set_name_fail(self):
        args = {
            "name": "test",
            "program_type": ProgramTypeEnum.GENERIC,
        }
        program = Program.factory(**args)
        with pytest.raises(ProgramNameDuplicate):
            program.set_name("test", 1)

    @pytest.mark.parametrize(
        "end_time,status",
        [
            pytest.param(
                pendulum.datetime(2023, 9, 1), ProgramStatus.ARCHIVED, id="invalid-status"
            ),
            pytest.param(
                pendulum.datetime(2022, 9, 1), ProgramStatus.ACTIVE, id="invalid-end-time"
            ),
        ],
    )
    def test_save_program_fail(self, end_time, status):
        name = "test"
        program_args = dict(
            general_fields=dict(
                program_priority=ProgramPriority.P1,
            )
        )
        program = Program.factory(name, ProgramTypeEnum.GENERIC)
        program.status = status
        program.end_date = end_time
        data = CreateUpdateProgram.from_dict(program_args)
        with pytest.raises(ProgramSaveViolation):
            program.set_program_fields(data)

    def test_create_dynamic(self):
        name = "test"
        program_args = dict(
            general_fields=dict(
                program_priority=ProgramPriority.P1,
            ),
            control_options=[ControlOptionsEnum.CSIP_AUS],
            dynamic_operating_envelope_fields=dict(
                limit_type=DOELimitType.REAL_POWER,
                calculation_frequency=DOECalculationFrequency.DAILY,
                control_type=[DOEControlType.DER_EXPORT_LIMIT, DOEControlType.DER_IMPORT_LIMIT],
                schedule_time_horizon_timeperiod=ScheduleTimeperiod.DAYS,
                schedule_time_horizon_number=4,
            ),
        )
        program: DynamicOperatingEnvelopesProgram = Program.factory(
            name, ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES
        )
        data = CreateUpdateProgram.from_dict(program_args)
        program.set_program_fields(data)
        assert isinstance(program, DynamicOperatingEnvelopesProgram)
        assert program.schedule_time_horizon_number == 4
        assert program.limit_type == DOELimitType.REAL_POWER
        assert program.calculation_frequency == DOECalculationFrequency.DAILY
        assert program.control_type == [
            DOEControlType.DER_EXPORT_LIMIT,
            DOEControlType.DER_IMPORT_LIMIT,
        ]
        assert program.schedule_time_horizon_timeperiod == ScheduleTimeperiod.DAYS

    @pytest.mark.parametrize(
        "holiday_payload",
        [
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
        ],
    )
    def test_save_holiday_exclusion(self, holiday_payload):
        program: DynamicOperatingEnvelopesProgram = Program.factory("test", ProgramTypeEnum.GENERIC)
        program.save_holiday_exclusion_program(holiday_payload)
        assert len(program.holiday_exclusions) == 1


class TestAvailOperatingMonths:
    def test_factory(self):
        data = dict(
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
        )
        AvailOperatingMonths.factory(data)

    def test_update_months(self):
        data = dict(
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
        )
        operating_months = AvailOperatingMonths.factory(data)
        new_months = dict(
            jan=False,
            feb=True,
            mar=False,
            apr=True,
            may=False,
            jun=True,
            jul=False,
            aug=True,
            sep=False,
            oct=True,
            nov=False,
            dec=True,
        )
        operating_months.update_months(new_months)
        assert operating_months.jan == new_months["jan"]
        assert operating_months.feb == new_months["feb"]
        assert operating_months.jun == new_months["jun"]
        assert operating_months.nov == new_months["nov"]


class TestDispatchOptOuts:
    @pytest.mark.parametrize(
        "opt_outs_dict",
        [
            pytest.param(
                [
                    {
                        "timeperiod": ProgramTimePeriod.DAY,
                        "value": 10,
                    },
                    {
                        "timeperiod": ProgramTimePeriod.MONTH,
                        "value": 10,
                    },
                ],
                id="new-opt-outs-valid",
            ),
            pytest.param(
                [
                    {
                        "timeperiod": ProgramTimePeriod.DAY,
                        "value": 10,
                    },
                    {
                        "timeperiod": ProgramTimePeriod.MONTH,
                        "value": 10,
                    },
                ],
                id="new-opt-outs-replace-old",
            ),
        ],
    )
    def test_update_opt_outs(self, opt_outs_dict):
        opt_outs = DispatchOptOut.bulk_factory(opt_outs_dict)
        got = len(opt_outs)
        expected = len(opt_outs_dict)
        assert got == expected

    def test_update_opt_outs_fail(self):
        """One timeperiod only per opt out. Should throw error."""
        opt_out_args = [
            {
                "timeperiod": ProgramTimePeriod.DAY,
                "value": 10,
            },
            {
                "timeperiod": ProgramTimePeriod.DAY,
                "value": 10,
            },
        ]
        with pytest.raises(OptOutTimeperiodUniqueViolation):
            DispatchOptOut.bulk_factory(opt_out_args)


class TestDispatchNotifications:
    @pytest.mark.parametrize(
        "dispatch_notifications,expected_count",
        [
            pytest.param(
                [
                    {"text": "first", "lead_time": DispatchLeadTimeEnum.ONE_HOUR},
                    {"text": "second", "lead_time": DispatchLeadTimeEnum.ONE_DAY},
                ],
                2,
                id="2-different-lead-times",
            ),
            pytest.param(
                [
                    {"text": "first", "lead_time": DispatchLeadTimeEnum.ONE_HOUR},
                    {"text": "second", "lead_time": DispatchLeadTimeEnum.ONE_HOUR},
                ],
                1,
                id="2-same-lead-times-save-1",
            ),
        ],
    )
    def test_update_notifications(self, dispatch_notifications, expected_count):
        notifications = DispatchNotification.bulk_factory(dispatch_notifications)
        got = len(notifications)
        assert got == expected_count


class TestAvailServiceWindows:
    @pytest.mark.parametrize(
        "service_window_dict,expected",
        [
            pytest.param(
                [
                    dict(
                        start_hour=12,
                        end_hour=15,
                        mon=True,
                        tue=True,
                        wed=True,
                        thu=True,
                        fri=True,
                        sat=True,
                        sun=True,
                    ),
                    dict(
                        start_hour=15,
                        end_hour=20,
                        mon=True,
                        tue=True,
                        wed=True,
                        thu=True,
                        fri=True,
                        sat=True,
                        sun=True,
                    ),
                    dict(
                        start_hour=21,
                        end_hour=23,
                        mon=True,
                        tue=True,
                        wed=True,
                        thu=True,
                        fri=True,
                        sat=True,
                        sun=True,
                    ),
                ],
                3,
                id="valid-service-window",
            ),
            pytest.param(
                [
                    dict(
                        start_hour=12,
                        end_hour=20,
                        mon=True,
                        tue=False,
                        wed=True,
                        thu=False,
                        fri=True,
                        sat=False,
                        sun=True,
                    ),
                    dict(
                        start_hour=10,
                        end_hour=20,
                        mon=False,
                        tue=True,
                        wed=False,
                        thu=True,
                        fri=False,
                        sat=True,
                        sun=False,
                    ),
                ],
                2,
                id="valid-service-window-time-overlap-different-days",
            ),
        ],
    )
    def test_update_service_windows(self, service_window_dict, expected):
        windows = AvailServiceWindow.bulk_factory(service_window_dict)
        got = len(windows)
        assert got == expected

    @pytest.mark.parametrize(
        "service_window_dict",
        [
            pytest.param(
                [
                    dict(
                        start_hour=12,
                        end_hour=15,
                        mon=True,
                        tue=True,
                        wed=True,
                        thu=True,
                        fri=True,
                        sat=True,
                        sun=True,
                    ),
                    dict(
                        start_hour=14,
                        end_hour=20,
                        mon=True,
                        tue=True,
                        wed=True,
                        thu=True,
                        fri=True,
                        sat=True,
                        sun=True,
                    ),
                ],
                id="overlapping-service-window",
            ),
            pytest.param(
                [
                    dict(
                        start_hour=9,
                        end_hour=20,
                        mon=False,
                        tue=False,
                        wed=True,
                        thu=False,
                        fri=False,
                        sat=False,
                        sun=False,
                    ),
                    dict(
                        start_hour=10,
                        end_hour=19,
                        mon=False,
                        tue=False,
                        wed=True,
                        thu=False,
                        fri=False,
                        sat=False,
                        sun=False,
                    ),
                ],
                id="service-window-time-inside-other-window",
            ),
        ],
    )
    def test_update_service_windows_fail(self, service_window_dict):
        with pytest.raises(ServiceWindowOverlapViolation):
            windows = AvailServiceWindow.bulk_factory(service_window_dict)
            got = len(windows)
            expected = 0
            assert got == expected
