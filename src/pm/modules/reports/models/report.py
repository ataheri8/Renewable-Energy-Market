from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, Numeric, UnicodeText, func
from sqlalchemy.orm import Mapped, relationship

from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.reports.enums import ReportTypeEnum
from shared.model import make_enum, make_timestamptz
from shared.system.database import Base
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class Report(Base):
    """Report model"""

    __tablename__ = "report"
    id: int = Column(Integer, primary_key=True)
    created_at: datetime = Column(
        make_timestamptz(),
        server_default=func.current_timestamp(),
        nullable=False,
        doc="Time at which the row was created.",
    )
    updated_at: datetime = Column(
        make_timestamptz(),
        server_default=func.current_timestamp(),
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Time at which the row was updated.",
    )
    report_type: ReportTypeEnum = Column(make_enum(ReportTypeEnum), nullable=False)
    program_id: int = Column(Integer, nullable=False)
    service_provider_id: int = Column(Integer, nullable=False)
    start_report_date: datetime = Column(make_timestamptz(), nullable=False)  # type: ignore
    end_report_date: datetime = Column(make_timestamptz(), nullable=False)  # type: ignore
    created_by: str = Column(UnicodeText, nullable=False)
    report_details: Optional[str] = Column(UnicodeText, nullable=False)
    user_id: Optional[int] = Column(Integer, nullable=False)
    total_events: Optional[int] = Column(Integer, nullable=False)
    average_event_duration: Optional[Decimal] = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False, default=0
    )
    dispatched_der: Optional[int] = Column(Integer, nullable=False)
    total_der_in_program: Optional[int] = Column(Integer, nullable=False)
    avail_flexibility_up: Optional[Decimal] = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False, default=0
    )
    avail_flexibility_down: Optional[Decimal] = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False, default=0
    )
    constraint_violations: Optional[int] = Column(Integer, nullable=False)
    constraint_warnings: Optional[int] = Column(Integer, nullable=False)


class ContractReportDetails(Base):
    __tablename__ = "contract_report_details"
    id: int = Column(Integer, primary_key=True)
    enrollment_date: datetime = Column(make_timestamptz(), nullable=False)  # type: ignore
    report_id: int = Column(Integer, ForeignKey("report.id"), nullable=False)
    der_id: str = Column(UnicodeText, ForeignKey("der_info.der_id"), nullable=False)
    service_provider_id: Optional[int] = Column(
        Integer, ForeignKey("service_provider.id"), nullable=False
    )
    contract_constraint_id: Optional[int] = Column(
        Integer, ForeignKey("contract_constraint_summary.id"), nullable=False
    )
    contract_constraints: Mapped[ContractConstraintSummary] = relationship(
        "ContractConstraintSummary", viewonly=True
    )


class EventDetails(Base):
    """Captures Event details for the purposes of report generation."""

    __tablename__ = "event_details"
    id: int = Column(Integer, primary_key=True)
    report_id: int = Column(Integer, ForeignKey("report.id"), nullable=False)
    dispatch_id: str = Column(UnicodeText, nullable=False)
    event_start: Optional[datetime] = Column(make_timestamptz(), nullable=False)  # type: ignore
    event_end: Optional[datetime] = Column(make_timestamptz(), nullable=False)
    number_of_dispatched_der: int = Column(Integer, nullable=False)
    number_of_opted_out_der: int = Column(Integer, nullable=False)
    requested_capacity: Decimal = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False, default=0
    )
    dispatched_capacity: Decimal = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False, default=0
    )
    event_status: str = Column(UnicodeText, nullable=False)


# ================ TYPING DEFINITIONS ================ #
