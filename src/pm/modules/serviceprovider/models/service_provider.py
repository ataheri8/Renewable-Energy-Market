from __future__ import annotations

from typing import Optional, TypedDict

from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.sqltypes import Boolean

from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from shared.model import CreatedAtUpdatedAtMixin, make_enum
from shared.system.database import Base
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ServiceProvider(CreatedAtUpdatedAtMixin, Base):
    __tablename__ = "service_provider"
    id: int = Column(Integer, primary_key=True)
    uuid = Column(UnicodeText, nullable=False, unique=True)
    name: str = Column(UnicodeText, nullable=False)
    service_provider_type: ServiceProviderType = Column(
        make_enum(ServiceProviderType), nullable=False
    )
    status: ServiceProviderStatus = Column(make_enum(ServiceProviderStatus), nullable=False)
    primary_contact: PrimaryContact = Column(JSONB, nullable=False)
    notification_contact: Optional[PrimaryContact] = Column(JSONB, nullable=True)
    address: Optional[Address] = Column(JSONB, nullable=True)
    deleted: bool = Column(Boolean, nullable=True, server_default="false")
    ders: Mapped[list[DerInfo]] = relationship(
        "DerInfo",
    )


class PrimaryContact(TypedDict):
    email_address: str
    phone_number: str


class Address(TypedDict):
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    zip_code: Optional[str]
    apt_unit: Optional[str]
