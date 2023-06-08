from __future__ import annotations

from datetime import datetime
from typing import Optional, TypedDict

from sqlalchemy import Column, ForeignKey, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship

from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.enums import (
    ContractStatus,
    ContractType,
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.progmgmt.models.program import Program
from pm.modules.serviceprovider.models import ServiceProvider
from shared.model import CreatedAtUpdatedAtMixin, make_enum
from shared.system.database import Base


class EnrollmentRequest(CreatedAtUpdatedAtMixin, Base):
    __tablename__ = "enrollment_request"
    id: int = Column(Integer, primary_key=True)
    program_id: int = Column(Integer, ForeignKey("program.id"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)
    der_id: str = Column(UnicodeText, ForeignKey("der_info.der_id"), nullable=False)
    enrollment_status: EnrollmentRequestStatus = Column(
        make_enum(EnrollmentRequestStatus), nullable=False
    )
    dynamic_operating_envelopes: Optional[DynamicOperatingEnvelopesDict] = Column(
        JSONB, nullable=True
    )
    demand_response: Optional[DemandResponseDict] = Column(JSONB, nullable=True)
    rejection_reason: Optional[EnrollmentRejectionReason] = Column(
        make_enum(EnrollmentRejectionReason), nullable=True
    )
    der: Mapped[DerInfo] = relationship("DerInfo")
    program: Mapped[Program] = relationship("Program")
    service_provider: Mapped[ServiceProvider] = relationship("ServiceProvider")
    contract: Mapped[Optional[Contract]] = relationship(
        "Contract",
        back_populates="enrollment_request",
        uselist=False,
    )

    @classmethod
    def get_report_headers(cls) -> list[str]:
        return list(
            EnrollmentRequest(
                program=Program(name="nothing"),
                enrollment_status=EnrollmentRequestStatus.ACCEPTED,
                created_at=datetime.now(),  # type: ignore
            )
            .get_report_row()
            .keys()
        )

    def get_report_row(self) -> dict[str, str]:
        return {
            "Program Name": self.program.name if self.program else "",
            "DER ID": self.der_id,
            "Service Provider ID": str(self.service_provider_id),
            "Enrollment Time": self.created_at.isoformat(),
            "Enrollment User ID": "",
            "Enrollment Status": self.enrollment_status.name,
            "Rejection Reason": self.rejection_reason.get_readable_text()
            if self.rejection_reason
            else "",
        }


class Contract(CreatedAtUpdatedAtMixin, Base):
    __tablename__ = "contract"
    id: int = Column(Integer, primary_key=True)
    program_id: int = Column(Integer, ForeignKey("program.id"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)
    der_id: str = Column(UnicodeText, ForeignKey("der_info.der_id"), nullable=False, index=True)
    contract_status: ContractStatus = Column(make_enum(ContractStatus), nullable=False)
    contract_type: ContractType = Column(make_enum(ContractType), nullable=False)
    enrollment_request_id = Column(
        Integer, ForeignKey("enrollment_request.id"), nullable=False, unique=True
    )
    enrollment_request: Mapped[EnrollmentRequest] = relationship(
        "EnrollmentRequest", lazy="noload", back_populates="contract"
    )
    dynamic_operating_envelopes: DynamicOperatingEnvelopesDict = Column(JSONB, nullable=True)
    demand_response: DemandResponseDict = Column(JSONB, nullable=True)
    der: Mapped[DerInfo] = relationship("DerInfo")
    program: Mapped[Program] = relationship("Program")
    service_provider: Mapped[ServiceProvider] = relationship("ServiceProvider")


class DynamicOperatingEnvelopesDict(TypedDict):
    default_limits_active_power_import_kw: float
    default_limits_active_power_export_kw: float
    default_limits_reactive_power_import_kw: float
    default_limits_reactive_power_export_kw: float


class DemandResponseDict(TypedDict):
    import_target_capacity: float
    export_target_capacity: float
