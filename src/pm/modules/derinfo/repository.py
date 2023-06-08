from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from dataclasses_json import DataClassJsonMixin
from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.models.enrollment import Contract, EnrollmentRequest
from shared.exceptions import Error
from shared.repository import SQLRepository
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class DerInfoRepository(SQLRepository):
    def upsert_der_from_kafka(self, payload: DerUpdate):
        values_dict = {
            "name": payload.name,
            "is_deleted": payload.is_deleted,
            "der_type": payload.der_type,
            "nameplate_rating": payload.nameplate_rating,
            "nameplate_rating_unit": payload.nameplate_rating_unit,
            "resource_category": payload.resource_category,
        }

        # Remove service provider association if the DER is deleted from DW
        if payload.is_deleted:
            values_dict["service_provider_id"] = None

        stmt = (
            insert(DerInfo)
            .values(**values_dict, der_id=payload.der_id)
            .on_conflict_do_update(index_elements=[DerInfo.der_id], set_=values_dict)
        )

        self.session.execute(stmt)

    def get_ders(self, service_provider=None, is_deleted=False) -> Sequence[DerInfo]:
        stmt = select(DerInfo).where(DerInfo.is_deleted == is_deleted)  # noqa: E712

        if service_provider is not None:
            stmt = stmt.where(DerInfo.service_provider_id == service_provider)  # noqa: E711

        return self.session.execute(stmt).unique().scalars().all()

    def get_der(
        self, id=None, der_id=None, service_provider=None, is_deleted=False
    ) -> Optional[DerInfo]:
        if id is None and der_id is None:
            return None

        stmt = select(DerInfo).where(DerInfo.is_deleted == is_deleted)  # noqa: E712

        if id:
            stmt = stmt.where(DerInfo.id == id)

        if der_id:
            stmt = stmt.where(DerInfo.der_id == der_id)

        if service_provider:
            stmt = stmt.where(DerInfo.service_provider_id == service_provider)  # noqa: E711

        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_der_or_raise_exception(
        self, id=None, der_id=None, service_provider=None, is_deleted=False
    ) -> DerInfo:
        der = self.get_der(id, der_id, service_provider, is_deleted)

        if der is None:
            raise DerNotFound(
                errors={"error": "Not Found"},
                message="DER was not found",  # noqa: E501
            )

        return der

    def get_ders_with_sp_no_contract(self) -> Sequence[DerInfo]:
        stmt = (
            select(DerInfo)
            .where(DerInfo.is_deleted == False)  # noqa: E712
            .where(DerInfo.service_provider_id != None)  # noqa: E711
            .join(Contract, DerInfo.der_id == Contract.der_id, isouter=True)
            .distinct(tuple_(DerInfo.der_id, Contract.contract_status))
        )
        return self.session.execute(stmt).unique().scalars().all()

    def get_ders_with_no_sp(self) -> Sequence[DerInfo]:
        stmt = (
            select(DerInfo)
            .where(DerInfo.is_deleted == False)  # noqa: E712
            .where(DerInfo.service_provider_id == None)  # noqa: E711
        )

        return self.session.execute(stmt).unique().scalars().all()

    def get_ders_in_program_with_enrollment(self, program_id: int) -> Sequence[DerInfo]:
        stmt = (
            select(DerInfo)
            .where(DerInfo.is_deleted == False)  # noqa: E712
            .where(DerInfo.service_provider_id != None)  # noqa: E711
            .join(EnrollmentRequest, DerInfo.der_id == EnrollmentRequest.der_id, isouter=True)
            .where(EnrollmentRequest.program_id == program_id)
        )

        return self.session.execute(stmt).unique().scalars().all()


@dataclass
class DerUpdate(DataClassJsonMixin):
    der_id: str
    name: str
    der_type: DerAssetType
    resource_category: DerResourceCategory
    nameplate_rating: float
    nameplate_rating_unit: LimitUnitType
    is_deleted: bool
    extra: Optional[dict] = None


class DerNotFound(Error):
    pass
