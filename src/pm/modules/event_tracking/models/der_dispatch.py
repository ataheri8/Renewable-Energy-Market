from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, Numeric, UnicodeText

from shared.model import make_timestamptz
from shared.system.database import Base


class DerDispatch(Base):
    """Captures DER dispatches.
    This is a result of a DER being dispatched and captures the information about a DER
    that participated in an event (multiple DERs can participate in an event)
    """

    __tablename__ = "der_dispatch"
    id: int = Column(Integer, primary_key=True)
    event_id: str = Column(UnicodeText, nullable=False)
    start_date_time: Optional[datetime] = Column(make_timestamptz(), nullable=False)  # type: ignore
    end_date_time: Optional[datetime] = Column(make_timestamptz(), nullable=False)  # type: ignore
    event_status: str = Column(
        UnicodeText, index=True, nullable=False, doc="status == '4' means opt out"
    )
    control_id: str = Column(
        UnicodeText,
        nullable=False,
        doc="The ID used to map this dispatch to response info",
    )
    control_type: str = Column(UnicodeText, nullable=False)
    control_command: Decimal = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False
    )
    contract_id: int = Column(Integer, ForeignKey("contract.id"), index=True, nullable=False)
    max_total_energy: Decimal = Column(  # type: ignore
        Numeric(precision=20, scale=4), nullable=False, default=0
    )
    cumulative_event_duration_mins: int = Column(Integer, nullable=False, default=0)
