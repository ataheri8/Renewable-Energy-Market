from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer

from shared.exceptions import Error
from shared.system.database import Base
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class AvailServiceWindow(Base):
    __tablename__ = "avail_service_window"
    id: int = Column(Integer, primary_key=True)
    program_id: int = Column(Integer, ForeignKey("program.id"), nullable=False)
    start_hour: int = Column(Integer)
    end_hour: int = Column(Integer)
    mon: bool = Column(Boolean)
    tue: bool = Column(Boolean)
    wed: bool = Column(Boolean)
    thu: bool = Column(Boolean)
    fri: bool = Column(Boolean)
    sat: bool = Column(Boolean)
    sun: bool = Column(Boolean)

    @property
    def days_list(self) -> list[bool]:
        """Lists the active days.
        0 is monday - 6 is sunday
        """
        return [self.mon, self.tue, self.wed, self.thu, self.fri, self.sat, self.sun]

    def check_overlap(self, window: AvailServiceWindow):
        """Checks the service window overlaps.
        Will raise a ServiceWindowOverlapViolation error if the windows overlap
        """
        for self_days, other_days in zip(self.days_list, window.days_list):
            if (
                self_days
                and other_days
                and self.start_hour < window.end_hour
                and self.end_hour > window.start_hour
            ):
                logger.error("Service windows must not overlap")
                raise ServiceWindowOverlapViolation("Service windows must not overlap")

    @classmethod
    def factory(cls, payload: dict) -> AvailServiceWindow:
        return cls(**payload)

    @classmethod
    def bulk_factory(cls, sw_dicts: list[dict]) -> list[AvailServiceWindow]:
        """Bulk create service windows for a program.
        If they overlap, an error will be thrown
        """
        service_windows: list[AvailServiceWindow] = [cls.factory(d) for d in sw_dicts]
        length = len(service_windows)
        # check none of the windows overlap
        for i in range(length):
            current_window = service_windows[i]
            for j in range(i + 1, length):
                to_check_window = service_windows[j]
                current_window.check_overlap(to_check_window)
        return service_windows


class ServiceWindowOverlapViolation(Error):
    pass
