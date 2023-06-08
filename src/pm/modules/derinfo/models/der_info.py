from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, UnicodeText, func
from sqlalchemy.sql.sqltypes import Boolean

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from shared.model import make_enum
from shared.system.database import Base


class DerInfo(Base):
    __tablename__ = "der_info"
    id: int = Column(Integer, primary_key=True)

    # Fields from DER Warehouse being filled by kafka message
    der_id: str = Column(UnicodeText, nullable=False, unique=True)
    name: str = Column(UnicodeText, nullable=False)
    is_deleted: bool = Column(Boolean, nullable=True, server_default="false")
    der_type: DerAssetType = Column(make_enum(DerAssetType), nullable=False)
    nameplate_rating: float = Column(  # type: ignore
        Numeric(precision=20, scale=4, asdecimal=False), nullable=False
    )
    nameplate_rating_unit: LimitUnitType = Column(make_enum(LimitUnitType), nullable=False)
    resource_category: DerResourceCategory = Column(make_enum(DerResourceCategory), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.current_timestamp(),
        onupdate=datetime.utcnow,
    )

    # PM Specific fields added on
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=True)
