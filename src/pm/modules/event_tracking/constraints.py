import abc
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.progmgmt.enums import ProgramTimePeriod
from pm.modules.progmgmt.models.program import MinMax, Program
from shared.system import loggingsys

WARN_PERCENT = 0.75

logger = loggingsys.get_logger(__name__)


@dataclass
class Constraint(abc.ABC):
    label: str
    timestamp: datetime
    constraint: Any
    event_property: Any
    value: Optional[int] = None
    has_warning: Optional[bool] = False
    has_violation: Optional[bool] = False

    @abc.abstractmethod
    def _violation_check(self) -> bool:
        pass

    @abc.abstractmethod
    def _warning_check(self) -> bool:
        pass

    def set_value(self, val: int):
        self.value = val
        self.has_violation = self._violation_check()
        self.has_warning = self._warning_check()

    @classmethod
    def factory(cls, label: str, timestamp: datetime, constraint: Any, event_property: Any):
        logger.info(
            f"Creating constraint {label} with value {constraint}, type({type(constraint)})"
        )
        if isinstance(constraint, (int, float, Decimal)):
            return NumberConstraint(
                label=label,
                timestamp=timestamp,
                constraint=constraint,
                event_property=event_property,
            )
        if isinstance(constraint, MinMax) and (
            constraint.min is not None or constraint.max is not None
        ):
            return MinMaxConstraint(
                label=label,
                timestamp=timestamp,
                constraint=constraint,
                event_property=event_property,
            )
        raise ValueError(f"Constraint {constraint} cannot be handled")


@dataclass
class NumberConstraint(Constraint):
    constraint: int | float | Decimal

    def _get_constraint_and_value(self) -> tuple[Decimal, Decimal]:
        """Returns the constraint and value as decimals.
        If the constraint value is negative, the constraint and value will be
        converted to positive values.
        """
        constraint = Decimal(self.constraint or 0)
        value = Decimal(self.value or 0)
        if constraint < 0:
            constraint = abs(constraint)
            value = abs(value)
        return constraint, value

    def _violation_check(self) -> bool:
        if self.value is None:
            return False
        constraint, value = self._get_constraint_and_value()
        return value > constraint

    def _warning_check(self) -> bool:
        if self.value is None:
            return False
        constraint, value = self._get_constraint_and_value()
        return value / constraint >= Decimal(WARN_PERCENT)


@dataclass
class MinMaxConstraint(Constraint):
    constraint: MinMax

    def _violation_check(self) -> bool:
        violation = False
        if self.value is not None and self.constraint.min:
            violation = self.value < self.constraint.min
        if not violation and self.value is not None and self.constraint.max:
            violation = self.value > self.constraint.max
        return violation

    def _warning_check(self) -> bool:
        warning = False
        if self.value is not None and self.constraint.min:
            warning = self.value < self.constraint.min
        if not warning and self.value is not None and self.constraint.max:
            warning = self.value / self.constraint.max >= WARN_PERCENT
        return warning


@dataclass
class ConstraintTypes:
    der_dispatch: list[Constraint] = field(default_factory=list)
    opt_out: list[Constraint] = field(default_factory=list)
    event_count: list[Constraint] = field(default_factory=list)

    def return_all_constraints(self) -> list[Constraint]:
        return self.der_dispatch + self.opt_out + self.event_count


class ConstraintsBuilder:
    """builder class to build constraints for a program."""

    def __init__(self):
        self.timeperiods: dict[ProgramTimePeriod, datetime] = {}

    def _get_constraints(
        self, event_property: Any, items: dict[str, Any], label: str
    ) -> list[Constraint]:
        constraints: list[Constraint] = []
        for k, v in items.items():
            property_name = f"{label}_{k}".lower()
            constraints.append(
                Constraint.factory(
                    label=property_name,
                    timestamp=self.timeperiods[ProgramTimePeriod[k]],
                    constraint=v,
                    event_property=event_property,
                )
            )
        return constraints

    def get_constraints(self, current_day: datetime, program: Program) -> ConstraintTypes:
        """Gets a list of constraints objects.
        These objects describe a single constraint for a program.
        """
        if not program.start_date:
            raise ValueError(f"Program {program.name} must have a start date!")
        self.timeperiods = ProgramTimePeriod.get_timestamps_for_periods(
            current_day, program.start_date
        )

        constraint_types = ConstraintTypes()

        if program.dispatch_constraints and program.dispatch_constraints.cumulative_event_duration:
            constraints = self._get_constraints(
                DerDispatch.cumulative_event_duration_mins,
                program.dispatch_constraints.cumulative_event_duration,
                "cumulative_event_duration",
            )
            constraint_types.der_dispatch += constraints

        if (
            program.dispatch_constraints
            and program.dispatch_constraints.max_number_of_events_per_timeperiod
        ):
            constraints = self._get_constraints(
                None,
                program.dispatch_constraints.max_number_of_events_per_timeperiod,
                "max_number_of_events_per_timeperiod",
            )
            constraint_types.event_count += constraints

        if (
            program.demand_management_constraints
            and program.demand_management_constraints.timeperiod
            and program.demand_management_constraints.max_total_energy_per_timeperiod
        ):
            key = program.demand_management_constraints.timeperiod.name
            value = program.demand_management_constraints.max_total_energy_per_timeperiod
            energy_items = {key: value}
            constraints = self._get_constraints(
                DerDispatch.max_total_energy, energy_items, "max_total_energy_per_timeperiod"
            )
            constraint_types.der_dispatch += constraints

        opt_outs = program.dispatch_max_opt_outs
        items = {opt_out.timeperiod.name: opt_out.value for opt_out in opt_outs}
        constraints = self._get_constraints(None, items, "opt_outs")
        constraint_types.opt_out += constraints

        return constraint_types

    @classmethod
    def build(cls, current_day: datetime, program: Program) -> ConstraintTypes:
        return cls().get_constraints(current_day, program)
