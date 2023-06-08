import datetime
from decimal import Decimal

import pendulum
import pytest

from pm.modules.event_tracking.builders.der_dispatch_dicts import (
    BuildDerDispatchDicts,
    CreateDerDispatchDict,
)


class TestBuildDispatchDicts:
    def test_build_one(self):
        """Ine event and no day boundary crossing."""
        START_UNIX_TIME = 1635489900
        END_UNIX_TIME = 1635497100

        dispatch_info = CreateDerDispatchDict(
            event_id="event-1",
            start_date_time=START_UNIX_TIME,
            end_date_time=END_UNIX_TIME,
            event_status="scheduled",
            control_command="1.00",
            control_type="kW % Rated Capacity",
            contract_id=1,
            control_id="B94E28E2C65547B3B1F9C096D4F8952B",
        )

        result = BuildDerDispatchDicts.build({1}, [dispatch_info])

        assert len(result) == 1
        assert result[0]["event_id"] == "event-1"
        assert result[0]["start_date_time"] == pendulum.from_timestamp(START_UNIX_TIME)
        assert result[0]["end_date_time"] == pendulum.from_timestamp(END_UNIX_TIME)
        assert result[0]["event_status"] == "scheduled"
        assert result[0]["control_command"] == Decimal("1.00")
        assert result[0]["control_type"] == "kW % Rated Capacity"
        assert result[0]["contract_id"] == 1
        assert result[0]["control_id"] == "B94E28E2C65547B3B1F9C096D4F8952B"
        assert result[0]["cumulative_event_duration_mins"] == 120
        assert result[0]["max_total_energy"] == Decimal("120.00")

    @pytest.mark.parametrize(
        "start,end,expected",
        [
            pytest.param(
                pendulum.datetime(2023, 10, 18, 23, 0, 0),
                pendulum.datetime(2023, 10, 19, 1, 0, 0),
                [
                    {
                        "control_command": Decimal("0.50"),
                        "cumulative_event_duration_mins": 60,
                        "max_total_energy": Decimal("60.00"),
                    },
                    {
                        "control_command": Decimal("0.50"),
                        "cumulative_event_duration_mins": 60,
                        "max_total_energy": Decimal("60.00"),
                    },
                ],
                id="even-split-day",
            ),
            pytest.param(
                pendulum.datetime(2023, 10, 18, 23, 0, 0),
                pendulum.datetime(2023, 10, 19, 3, 0, 0),
                [
                    {
                        "control_command": Decimal("0.25"),
                        "cumulative_event_duration_mins": 60,
                        "max_total_energy": Decimal("60.00"),
                    },
                    {
                        "control_command": Decimal("0.75"),
                        "cumulative_event_duration_mins": 180,
                        "max_total_energy": Decimal("180.00"),
                    },
                ],
                id="thirds-split-day",
            ),
            pytest.param(
                pendulum.datetime(2023, 10, 18, 0, 0, 0),
                pendulum.datetime(2023, 10, 19, 0, 0, 0),
                [
                    {
                        "control_command": Decimal("1.00"),
                        "cumulative_event_duration_mins": 1440,
                        "max_total_energy": Decimal("1440.00"),
                    }
                ],
                id="even-split-full-day",
            ),
            pytest.param(
                pendulum.datetime(2023, 10, 18, 0, 0, 0),
                pendulum.datetime(2023, 10, 20, 0, 0, 0),
                [
                    {
                        "control_command": Decimal("0.50"),
                        "cumulative_event_duration_mins": 1440,
                        "max_total_energy": Decimal("1440.00"),
                    },
                    {
                        "control_command": Decimal("0.50"),
                        "cumulative_event_duration_mins": 1440,
                        "max_total_energy": Decimal("1440.00"),
                    },
                ],
                id="even-split-2-full-days",
            ),
        ],
    )
    def test_build_one_split_day(self, start: datetime, end: datetime, expected: list[dict]):
        """One event with a day boundary crossing."""
        START_UNIX_TIME = start.int_timestamp
        END_UNIX_TIME = end.int_timestamp

        dispatch_info = CreateDerDispatchDict(
            event_id="event-1",
            start_date_time=START_UNIX_TIME,
            end_date_time=END_UNIX_TIME,
            event_status="scheduled",
            control_command="1.00",
            control_type="kW % Rated Capacity",
            contract_id=1,
            control_id="B94E28E2C65547B3B1F9C096D4F8952B",
        )

        result = BuildDerDispatchDicts.build({1}, [dispatch_info])

        assert len(result) == len(expected)
        for got, exp in zip(result, expected):
            assert got["event_id"] == "event-1"
            assert got["event_status"] == "scheduled"
            assert got["control_command"] == exp["control_command"]
            assert got["control_type"] == "kW % Rated Capacity"
            assert got["contract_id"] == 1
            assert got["control_id"] == "B94E28E2C65547B3B1F9C096D4F8952B"
            assert got["cumulative_event_duration_mins"] == exp["cumulative_event_duration_mins"]
            assert got["max_total_energy"] == exp["max_total_energy"]
