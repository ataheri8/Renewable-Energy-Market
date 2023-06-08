from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from sqlalchemy import Boolean, Column, Integer, UnicodeText

from shared.model import make_timestamptz
from shared.system.database import Base

OPT_OUT_STATUS_CODE = 4


class CreateDerResponseDict(TypedDict):
    der_id: str
    der_response_status: int
    der_response_time: datetime
    control_id: str
    is_opt_out: bool


class DerResponse(Base):
    """Captures DER response. This is a result of a DER responding to a dispatch."""

    __tablename__ = "der_response"
    id: int = Column(Integer, primary_key=True)
    der_id: str = Column(UnicodeText, nullable=False)
    der_response_status: int = Column(Integer, nullable=False)
    der_response_time: datetime = Column(make_timestamptz(), nullable=False)
    control_id: str = Column(
        UnicodeText,
        index=True,
        nullable=False,
        doc="The ID used to map this response to dispatch info",
    )
    is_opt_out: bool = Column(Boolean, nullable=False)
