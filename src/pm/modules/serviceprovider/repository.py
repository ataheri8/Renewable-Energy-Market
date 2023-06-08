from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import and_, select, update
from sqlalchemy.orm import joinedload

from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.serviceprovider.enums import ServiceProviderStatus
from pm.modules.serviceprovider.models.service_provider import ServiceProvider
from shared.exceptions import Error
from shared.repository import SQLRepository
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ServiceProviderRepository(SQLRepository):
    """Deals with ALL writes and reads related to commands & queries to the DB"""

    def get_all(self, load_ders=False) -> Sequence[ServiceProvider]:
        stmt = (
            select(ServiceProvider)
            .where(ServiceProvider.deleted == False)  # noqa: E712
            .order_by(ServiceProvider.id)
        )
        if load_ders:
            stmt = stmt.options(joinedload(ServiceProvider.ders))
        data = self.session.execute(stmt).unique().scalars().all()
        for svc in data:
            ders = []
            for der in svc.ders:
                if der.is_deleted is False:
                    ders.append(der)
            svc.ders = ders
        return data

    def get_service_provider(
        self, service_provider_id: int, load_ders=False
    ) -> Optional[ServiceProvider]:
        stmt = (
            select(ServiceProvider)
            .where(ServiceProvider.deleted == False)  # noqa: E712
            .where(ServiceProvider.id == service_provider_id)
        )
        if load_ders:
            stmt = stmt.options(joinedload(ServiceProvider.ders))

        svc = self.session.execute(stmt).unique().scalar_one_or_none()
        ders = []
        if svc:
            for der in svc.ders:
                if der.is_deleted is False:
                    ders.append(der)
            svc.ders = ders
        return svc

    def get_service_provider_or_raise(
        self, service_provider_id: int, load_ders=False, include_inactive=True
    ) -> ServiceProvider:
        service_provider = self.get_service_provider(service_provider_id, load_ders)
        if not service_provider:
            raise ServiceProviderNotFound(
                errors={"error": "Not Found"},
                message=f"Service Provider with id {service_provider_id} is not found",
            )
        if not include_inactive:
            if service_provider.status == ServiceProviderStatus.INACTIVE:  # type: ignore
                raise ServiceProviderNotFound(
                    errors={"error": "Not Active"},
                    message=f"Service Provider with id {service_provider_id} is not active",
                )
        return service_provider

    def count_by_name(self, name: str) -> int:
        stmt = select(ServiceProvider.id).where(
            and_(ServiceProvider.name == name, ServiceProvider.deleted == False)  # noqa: E712
        )
        return self.count(stmt)

    def remove_service_provider(self, svc_provider_id: int, der_id: int):
        stmt = (
            update(DerInfo)
            .where(DerInfo.service_provider_id == svc_provider_id)
            .where(DerInfo.id == der_id)
            .values(service_provider_id=None)
        )
        self.session.execute(stmt)

    def get_der(self, svc_provider_id: int, der_id: int) -> Optional[DerInfo]:
        stmt = (
            select(DerInfo)
            .where(DerInfo.service_provider_id == svc_provider_id)
            .where(DerInfo.id == der_id)
            .where(DerInfo.is_deleted == False)  # noqa: E712
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_der_or_raise(self, svc_provider_id: int, der_id: int) -> DerInfo:
        der = self.get_der(svc_provider_id, der_id)
        if not der:
            raise ServiceProviderDerAssociationNotFound(
                errors={"error": "Not Found"},
                message=f"Association of Service Provider with id {svc_provider_id} "
                f"with Der with id {der_id} is not found",
                # noqa: E501
            )
        return der

    def get_der_with_uuid(self, svc_provider_id: int, der_rdf_id: str) -> Optional[DerInfo]:
        stmt = (
            select(DerInfo)
            .where(DerInfo.service_provider_id == svc_provider_id)
            .where(DerInfo.der_id == der_rdf_id)
            .where(DerInfo.is_deleted == False)  # noqa: E712
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_der_without_serviceprovider(self, der_id: str) -> Optional[DerInfo]:  # type: ignore
        stmt = (
            select(DerInfo)
            .where(DerInfo.der_id == der_id)
            .where(DerInfo.service_provider_id == None)  # noqa: E711
            .where(DerInfo.is_deleted == False)  # noqa: E712
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def update_der(self, service_provider_id: int, der_id):  # type: ignore
        existing_der = self.get_der_without_serviceprovider(der_id=der_id)
        if not existing_der:
            raise ServiceProviderDerAssociationNotFound(
                errors={"error": "Not Found"},
                message=f"Association of Service Provider with id {service_provider_id} with Der with id {der_id} is not found",  # noqa: E501
            )

        stmt = (
            update(DerInfo)
            .where(DerInfo.der_id == der_id)
            .values(service_provider_id=service_provider_id)
        )
        self.session.execute(stmt)

    def get_ders_service_provider(self, service_provider_id: int) -> Sequence[DerInfo]:
        stmt = (
            select(DerInfo)
            .where(DerInfo.service_provider_id == service_provider_id)
            .where(DerInfo.is_deleted == False)  # noqa: E712
        )
        return self.session.execute(stmt).unique().scalars().all()


class ServiceProviderNotFound(Error):
    pass


class ServiceProviderDerAssociationNotFound(Error):
    pass


class ServiceProviderNoDerAssociationFound(Error):
    pass


class InvalidCSVColumns(Error):
    def __init__(self):
        self.message = "Invalid Column Type must be 'der_rdf_id'"
        super().__init__(self.message)
