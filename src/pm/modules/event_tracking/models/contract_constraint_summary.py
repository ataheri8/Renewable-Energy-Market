from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)

from pm.modules.event_tracking.constraints import Constraint
from shared.model import CreatedAtUpdatedAtMixin
from shared.system.database import Base


class ContractConstraintSummary(CreatedAtUpdatedAtMixin, Base):
    """Summarises the current state of contract constraints.

    Will be calculated every day
    """

    __tablename__ = "contract_constraint_summary"
    id: int = Column(Integer, primary_key=True)
    contract_id: int = Column(Integer, ForeignKey("contract.id"), nullable=False)
    day: date = Column(Date, nullable=False)

    # cumulative event duration
    cumulative_event_duration_day: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    cumulative_event_duration_day_warning: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_day_violation: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_week: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    cumulative_event_duration_week_warning: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_week_violation: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_month: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    cumulative_event_duration_month_warning: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_month_violation: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_year: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    cumulative_event_duration_year_warning: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_year_violation: Optional[bool] = Column(Boolean, nullable=True)
    cumulative_event_duration_program_duration: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    cumulative_event_duration_program_duration_warning: Optional[bool] = Column(
        Boolean, nullable=True
    )
    cumulative_event_duration_program_duration_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )
    # max_number_of_events_per_timeperiod
    max_number_of_events_per_timeperiod_day: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    max_number_of_events_per_timeperiod_day_warning: Optional[bool] = Column(Boolean, nullable=True)
    max_number_of_events_per_timeperiod_day_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_week: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    max_number_of_events_per_timeperiod_week_warning: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_week_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_month: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    max_number_of_events_per_timeperiod_month_warning: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_month_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_year: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    max_number_of_events_per_timeperiod_year_warning: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_year_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_program_duration: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    max_number_of_events_per_timeperiod_program_duration_warning: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_number_of_events_per_timeperiod_program_duration_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )
    # opt_outs
    opt_outs_day: Optional[int] = Column(Integer, nullable=True, info={"is_value": True})
    opt_outs_day_warning: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_day_violation: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_week: Optional[int] = Column(Integer, nullable=True, info={"is_value": True})
    opt_outs_week_warning: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_week_violation: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_month: Optional[int] = Column(Integer, nullable=True, info={"is_value": True})
    opt_outs_month_warning: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_month_violation: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_year: Optional[int] = Column(Integer, nullable=True, info={"is_value": True})
    opt_outs_year_warning: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_year_violation: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_program_duration: Optional[int] = Column(
        Integer, nullable=True, info={"is_value": True}
    )
    opt_outs_program_duration_warning: Optional[bool] = Column(Boolean, nullable=True)
    opt_outs_program_duration_violation: Optional[bool] = Column(Boolean, nullable=True)
    # max_total_energy
    max_total_energy_per_timeperiod_day = Column(
        Numeric(precision=20, scale=4), nullable=True, info={"is_value": True}
    )
    max_total_energy_per_timeperiod_day_warning: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_day_violation: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_week = Column(
        Numeric(precision=20, scale=4), nullable=True, info={"is_value": True}
    )
    max_total_energy_per_timeperiod_week_warning: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_week_violation: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_month = Column(
        Numeric(precision=20, scale=4), nullable=True, info={"is_value": True}
    )
    max_total_energy_per_timeperiod_month_warning: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_month_violation: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_year = Column(
        Numeric(precision=20, scale=4), nullable=True, info={"is_value": True}
    )
    max_total_energy_per_timeperiod_year_warning: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_year_violation: Optional[bool] = Column(Boolean, nullable=True)
    max_total_energy_per_timeperiod_program_duration = Column(
        Numeric(precision=20, scale=4), nullable=True, info={"is_value": True}
    )
    max_total_energy_per_timeperiod_program_duration_warning: Optional[bool] = Column(
        Boolean, nullable=True
    )
    max_total_energy_per_timeperiod_program_duration_violation: Optional[bool] = Column(
        Boolean, nullable=True
    )

    __table_args__ = (UniqueConstraint("contract_id", "day"),)

    @property
    def processed_summary_dict(self):
        """Transform a row into processed dictionary"""
        constraint_fields: dict = {
            "cumulative_event_duration": {},
            "max_number_of_events_per_timeperiod": {},
            "max_total_energy_per_timeperiod": {},
            "opt_outs": {},
        }
        value_columns = list(
            map(
                lambda x: str(x.name),
                filter(
                    lambda x: x.info.get("is_value", False),
                    ContractConstraintSummary.__table__.columns,
                ),
            )
        )
        for field in constraint_fields:
            for column in value_columns:
                if field in column and getattr(self, column, None) is not None:
                    child_field = column.replace(f"{field}_", "").upper()
                    constraint_fields[field][child_field] = {
                        "number": getattr(self, column),
                        "warning": getattr(self, f"{column}_warning"),
                        "violation": getattr(self, f"{column}_violation"),
                    }
        return constraint_fields

    @classmethod
    def create_from_constraints(
        cls, contract_id: int, day: date, constraints: list[Constraint]
    ) -> ContractConstraintSummary:
        """Create a ContractConstraintSummary from a list of ContractConstraint"""
        constraint_dict: dict[str, Any] = {}
        for col in ContractConstraintSummary.__table__.columns:
            if col.name not in ["id", "contract_id", "day", "created_at", "updated_at"]:
                constraint_dict[col.name] = None
        for c in constraints:
            constraint_dict[c.label] = c.value
            constraint_dict[f"{c.label}_warning"] = c.has_warning
            constraint_dict[f"{c.label}_violation"] = c.has_violation
        return cls(**constraint_dict, contract_id=contract_id, day=day)
