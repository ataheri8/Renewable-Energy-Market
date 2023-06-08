from datetime import datetime

import pendulum
import pytest
from sqlalchemy.orm.attributes import InstrumentedAttribute

from pm.modules.event_tracking.constraints import (
    Constraint,
    ConstraintsBuilder,
    MinMaxConstraint,
    NumberConstraint,
)
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.progmgmt.enums import ProgramTimePeriod
from pm.modules.progmgmt.models.dispatch_opt_out import DispatchOptOut
from pm.modules.progmgmt.models.program import (
    Constraints,
    DemandManagementConstraints,
    MinMax,
    Program,
)


class TestConstraints:
    def test_set_value(self):
        int_constraint = NumberConstraint(
            label="test_constraint",
            timestamp=datetime.now(),
            constraint=10,
            event_property="test_event_property",
        )
        assert not int_constraint.has_violation
        int_constraint.set_value(5)
        assert not int_constraint.has_violation
        int_constraint.set_value(15)
        assert int_constraint.has_violation

    def test_minmax_constraint(self):
        minmax_constraint = MinMaxConstraint(
            label="test_constraint",
            timestamp=datetime.now(),
            constraint=MinMax(min=5, max=15),
            event_property="test_event_property",
        )
        assert not minmax_constraint.has_violation
        minmax_constraint.set_value(10)
        assert not minmax_constraint.has_violation
        minmax_constraint.set_value(5)
        assert not minmax_constraint.has_violation
        minmax_constraint.set_value(20)
        assert minmax_constraint.has_violation
        minmax_constraint.set_value(4)
        assert minmax_constraint.has_violation

    def test_factory_method(self):
        # Test integer constraint
        int_constraint = Constraint.factory(
            label="test_constraint",
            timestamp=datetime.now(),
            constraint=10,
            event_property="test_event_property",
        )
        assert isinstance(int_constraint, NumberConstraint)
        # Test min-max constraint
        minmax_constraint = Constraint.factory(
            label="test_constraint",
            timestamp=datetime.now(),
            constraint=MinMax(min=5, max=15),
            event_property="test_event_property",
        )
        assert isinstance(minmax_constraint, MinMaxConstraint)

    def test_factory_method_valueerror(self):
        with pytest.raises(ValueError):
            Constraint.factory(
                label="test_constraint",
                timestamp=datetime.now(),
                constraint="invalid_constraint",
                event_property="test_event_property",
            )


class TestConstraintsBuilder:
    def test_get_constraints(self):
        program = Program(start_date=pendulum.now().subtract(days=7))
        # 7 constraints
        program.dispatch_constraints = Constraints.from_dict(
            dict(
                max_number_of_events_per_timeperiod={"DAY": 5, "WEEK": 15, "MONTH": 30, "YEAR": 60},
                cumulative_event_duration={
                    "WEEK": {"min": 10, "max": 100},
                    "MONTH": {"min": 20, "max": 240},
                    "YEAR": {"min": 120, "max": 480},
                },
            )
        )
        # 1 constraint
        program.demand_management_constraints = DemandManagementConstraints(
            max_total_energy_per_timeperiod=100, timeperiod=ProgramTimePeriod.DAY
        )

        # 3 constraints
        program.dispatch_max_opt_outs = [
            DispatchOptOut(timeperiod=ProgramTimePeriod.DAY, value=1),
            DispatchOptOut(timeperiod=ProgramTimePeriod.WEEK, value=2),
            DispatchOptOut(timeperiod=ProgramTimePeriod.MONTH, value=5),
        ]

        expected_constraints_count = 11

        constraint_types = ConstraintsBuilder.build(pendulum.now(), program)
        constraints = constraint_types.return_all_constraints()
        assert len(constraints) == expected_constraints_count
        for c in constraints:
            assert isinstance(c, Constraint)

        opt_out_constraints = [c for c in constraints if c.label.startswith("opt_outs")]
        for c in opt_out_constraints:
            assert isinstance(c.constraint, int)
            assert isinstance(c.timestamp, datetime)
            assert c.event_property is None
            assert c.label in [
                "opt_outs_day",
                "opt_outs_week",
                "opt_outs_month",
            ]

        cumulative_event_duration_constraints = [
            c for c in constraints if c.label.startswith("cumulative_event_duration")
        ]
        for c in cumulative_event_duration_constraints:
            assert isinstance(c.constraint, MinMax)
            assert isinstance(c.timestamp, datetime)
            assert isinstance(c.event_property, InstrumentedAttribute)
            assert c.event_property.key == DerDispatch.cumulative_event_duration_mins.key
            assert c.label in [
                "cumulative_event_duration_week",
                "cumulative_event_duration_month",
                "cumulative_event_duration_year",
            ]

        max_number_of_events_constraints = [
            c for c in constraints if c.label.startswith("max_number_of_events_per_timeperiod")
        ]
        for c in max_number_of_events_constraints:
            assert isinstance(c.constraint, int)
            assert isinstance(c.timestamp, datetime)
            assert c.event_property is None
            assert c.label in [
                "max_number_of_events_per_timeperiod_day",
                "max_number_of_events_per_timeperiod_week",
                "max_number_of_events_per_timeperiod_month",
                "max_number_of_events_per_timeperiod_year",
            ]

        max_total_energy_constraints = [
            c for c in constraints if c.label.startswith("max_total_energy_per_timeperiod")
        ]
        for c in max_total_energy_constraints:
            assert isinstance(c.constraint, int)
            assert isinstance(c.timestamp, datetime)
            assert isinstance(c.event_property, InstrumentedAttribute)
            assert c.event_property.key == DerDispatch.max_total_energy.key
            assert c.label in ["max_total_energy_per_timeperiod_day"]
