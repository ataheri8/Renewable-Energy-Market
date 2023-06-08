from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer

from shared.system.database import Base


class AvailOperatingMonths(Base):
    __tablename__ = "avail_operating_months"
    id: int = Column(Integer, primary_key=True)
    program_id: int = Column(Integer, ForeignKey("program.id"), nullable=False)
    jan: bool = Column(Boolean, nullable=True)
    feb: bool = Column(Boolean, nullable=True)
    mar: bool = Column(Boolean, nullable=True)
    apr: bool = Column(Boolean, nullable=True)
    may: bool = Column(Boolean, nullable=True)
    jun: bool = Column(Boolean, nullable=True)
    jul: bool = Column(Boolean, nullable=True)
    aug: bool = Column(Boolean, nullable=True)
    sep: bool = Column(Boolean, nullable=True)
    oct: bool = Column(Boolean, nullable=True)
    nov: bool = Column(Boolean, nullable=True)
    dec: bool = Column(Boolean, nullable=True)

    def update_months(self, data: dict):
        for month, value in data.items():
            if hasattr(self, month):
                setattr(self, month, value)

    @classmethod
    def factory(cls, payload: dict) -> AvailOperatingMonths:
        return cls(**payload)
