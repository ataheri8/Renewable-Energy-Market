from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, UnicodeText

from pm.modules.progmgmt.enums import DispatchLeadTimeEnum
from shared.system.database import Base


class DispatchNotification(Base):
    __tablename__ = "dispatch_notification"
    id: int = Column(Integer, primary_key=True)
    program_id: int = Column(Integer, ForeignKey("program.id"), nullable=False)
    text: str = Column(UnicodeText)
    lead_time: int = Column(Integer)

    @classmethod
    def factory(cls, payload: dict) -> DispatchNotification:
        return cls(**payload)

    @classmethod
    def bulk_factory(cls, notification_dicts: list[dict]) -> list[DispatchNotification]:
        lead_time_set: set[DispatchLeadTimeEnum] = set()
        notifications: list[DispatchNotification] = []
        for notification_dict in notification_dicts:
            if notification_dict["lead_time"] in lead_time_set:
                # we can just ignore duplicates in this case since there is only 1 value
                continue
            lead_time_set.add(notification_dict["lead_time"])
            notifications.append(cls.factory(notification_dict))
        return notifications
