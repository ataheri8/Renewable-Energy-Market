from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer

from pm.modules.progmgmt.enums import ProgramTimePeriod
from shared.exceptions import Error
from shared.model import make_enum
from shared.system.database import Base


class DispatchOptOut(Base):
    __tablename__ = "dispatch_opt_out"
    id: int = Column(Integer, primary_key=True)
    program_id: int = Column(Integer, ForeignKey("program.id"), nullable=False)
    timeperiod: ProgramTimePeriod = Column(make_enum(ProgramTimePeriod), nullable=False)
    value: int = Column(Integer)

    @classmethod
    def factory(cls, payload: dict) -> DispatchOptOut:
        return cls(**payload)

    @classmethod
    def bulk_factory(cls, opt_out_dicts: list[dict]) -> list[DispatchOptOut]:
        timeperiod_set: set[ProgramTimePeriod] = set()
        opt_outs: list[DispatchOptOut] = []
        for opt_out in opt_out_dicts:
            if opt_out["timeperiod"] in timeperiod_set:
                err = {"dispatch_max_opt_outs": ["Timeperiod must be unique"]}
                raise OptOutTimeperiodUniqueViolation("Timeperiod must be unique", errors=err)
            timeperiod_set.add(opt_out["timeperiod"])
            opt_outs.append(cls.factory(opt_out))
        return opt_outs


class OptOutTimeperiodUniqueViolation(Error):
    pass
