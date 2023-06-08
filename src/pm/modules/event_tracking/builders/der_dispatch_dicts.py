from datetime import datetime
from decimal import Decimal
from typing import Generator, TypedDict

import pendulum


class CreateDerDispatchDict(TypedDict):
    event_id: str
    start_date_time: int
    end_date_time: int
    control_command: str
    event_status: str
    control_type: str
    contract_id: int
    control_id: str


class InsertDerDispatchDict(TypedDict):
    event_id: str
    start_date_time: datetime
    end_date_time: datetime
    control_command: Decimal
    event_status: str
    control_type: str
    contract_id: int
    control_id: str
    max_total_energy: Decimal
    cumulative_event_duration_mins: int


class BuildDerDispatchDicts(object):
    def calculate_cumulative_event_duration(
        self, start_date_time: pendulum.DateTime, end_date_time: pendulum.DateTime
    ) -> int:
        return int((end_date_time - start_date_time).total_seconds() / 60)

    def calculate_max_total_energy(self, control_command: Decimal, time_mins: int) -> Decimal:
        return Decimal(control_command) * Decimal(time_mins)

    def _check_day_boundary_crossing(
        self, start_date_time: pendulum.DateTime, end_date_time: pendulum.DateTime
    ) -> bool:
        """Check if the start and end times go over a day boundary.
        If end date is the midnight the next day, then it not a day boundary crossing.

        For example, 2023-01-01:00:00:00 and 2023-01-02:00:00:00 is not a day boundary crossing.
        """
        return start_date_time.date() != end_date_time.subtract(seconds=1).date()

    def _time_weighted_average(
        self,
        start_time_mins: int,
        end_time_mins: int,
        total_time_mins: int,
        val: str | int | Decimal | float,
    ) -> Decimal:
        """Calculate the time weighted average of a value."""
        interval = Decimal(end_time_mins - start_time_mins)
        return (Decimal(val) * interval) / Decimal(total_time_mins)

    def _split_interval_into_days(
        self, start_time: pendulum.DateTime, end_time: pendulum.DateTime
    ) -> list[pendulum.DateTime]:
        """Takes a start time and end time and splits them into days."""
        start_date = start_time.date()
        end_date = end_time.subtract(seconds=1).date()
        split_dates = []
        while start_date < end_date:
            start_date += pendulum.duration(days=1)
            split_datetime = pendulum.datetime(
                year=start_date.year, month=start_date.month, day=start_date.day
            )
            split_dates.append(split_datetime)
        return split_dates

    def _split_events_by_day(
        self,
        data: CreateDerDispatchDict,
        max_total_energy: Decimal,
        cumulative_event_duration: int,
        control_command: Decimal,
        start_date_time: pendulum.DateTime,
        end_date_time: pendulum.DateTime,
    ) -> Generator[InsertDerDispatchDict, None, None]:
        """Split an event into multiple events if it crosses a day boundary."""
        split_times = self._split_interval_into_days(start_date_time, end_date_time)
        times = [start_date_time] + split_times + [end_date_time]
        total_time_mins = int(end_date_time.timestamp()) - int(start_date_time.timestamp())
        for i in range(0, len(times) - 1):
            interval_start = int(times[i].timestamp())
            interval_end = int(times[i + 1].timestamp())

            weighted_event_duration = self._time_weighted_average(
                interval_start,
                interval_end,
                total_time_mins,
                cumulative_event_duration,
            )
            weighted_max_total_energy = self._time_weighted_average(
                interval_start, interval_end, total_time_mins, max_total_energy
            )
            weighted_control_command = self._time_weighted_average(
                interval_start, interval_end, total_time_mins, control_command
            )
            yield self._make_dict(
                data=data,
                cumulative_event_duration_mins=int(weighted_event_duration),
                max_total_energy=weighted_max_total_energy,
                control_command=weighted_control_command,
                start_date_time=times[i],
                end_date_time=times[i + 1],
            )

    def _make_dict(
        self,
        data: CreateDerDispatchDict,
        max_total_energy: Decimal,
        cumulative_event_duration_mins: int,
        control_command: Decimal,
        start_date_time: pendulum.DateTime,
        end_date_time: pendulum.DateTime,
    ) -> InsertDerDispatchDict:
        return {
            "cumulative_event_duration_mins": cumulative_event_duration_mins,
            "max_total_energy": max_total_energy,
            "control_command": control_command,
            "start_date_time": start_date_time,
            "end_date_time": end_date_time,
            "event_status": data["event_status"],
            "control_type": data["control_type"],
            "contract_id": data["contract_id"],
            "control_id": data["control_id"],
            "event_id": data["event_id"],
        }

    def create_dicts(self, data: CreateDerDispatchDict) -> list[InsertDerDispatchDict]:
        """Create a dict with the correct values for the database.

        Checks if the start and end times go over a day boundary. If they do,
        we want to create two separate events with max total energy, cumulative event duration,
        and control command split as time weighted values.

        Most events will not go over a day boundary.
        """
        control_command = Decimal(data["control_command"])
        start_date_time = pendulum.from_timestamp(data["start_date_time"])
        end_date_time = pendulum.from_timestamp(data["end_date_time"])

        cumulative_event_duration_mins = self.calculate_cumulative_event_duration(
            start_date_time, end_date_time
        )
        max_total_energy = self.calculate_max_total_energy(
            control_command, cumulative_event_duration_mins
        )
        dispatches: list[InsertDerDispatchDict] = []
        if self._check_day_boundary_crossing(start_date_time, end_date_time):
            for event in self._split_events_by_day(
                data,
                max_total_energy,
                cumulative_event_duration_mins,
                control_command,
                start_date_time,
                end_date_time,
            ):
                dispatches.append(event)
        else:
            # nearly all events should fall into this category
            dispatches.append(
                self._make_dict(
                    data=data,
                    cumulative_event_duration_mins=cumulative_event_duration_mins,
                    max_total_energy=max_total_energy,
                    control_command=control_command,
                    start_date_time=start_date_time,
                    end_date_time=end_date_time,
                )
            )
        return dispatches

    @classmethod
    def build(
        cls, contract_id_set: set[int], data: list[CreateDerDispatchDict]
    ) -> list[InsertDerDispatchDict]:
        """Builds a list of der dispatch dicts.

        This allows us to skip the ORM when inserting data into the database,
        which is faster.
        """
        builder = cls()
        dispatches: list[InsertDerDispatchDict] = []
        for d in data:
            if d["contract_id"] not in contract_id_set:
                continue
            dispatches += builder.create_dicts(d)  # type: ignore
        return dispatches
