from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.modules.serviceprovider.models.service_provider import (
    Address,
    PrimaryContact,
    ServiceProvider,
)
from shared.exceptions import Error
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ServiceProviderService:
    def set_service_provider_fields(
        self, service_provider: ServiceProvider, data: CreateUpdateServiceProvider
    ) -> ServiceProvider:
        """Validates and sets a service provider's fields"""
        general_fields = data.general_fields
        if general_fields.service_provider_type is not None:
            service_provider.service_provider_type = general_fields.service_provider_type
        if general_fields.status is not None:
            service_provider.status = general_fields.status
        if data.primary_contact is not None:
            service_provider.primary_contact = data.primary_contact
        if data.notification_contact:
            service_provider.notification_contact = data.notification_contact
        if data.address:
            service_provider.address = data.address
        logger.info("Saved Service Provider")
        return service_provider

    def delete_service_provider(self, service_provider: ServiceProvider) -> ServiceProvider:
        """Deletes a Service Provider"""
        self.disable_service_provider(service_provider)
        service_provider.deleted = True
        service_provider.ders = []
        logger.info("Deleted Service Provider")
        return service_provider

    def enable_service_provider(self, service_provider: ServiceProvider) -> ServiceProvider:
        """Enables a Service Provider"""
        service_provider.status = ServiceProviderStatus.ACTIVE
        logger.info("Enabled Service Provider")
        return service_provider

    def disable_service_provider(self, service_provider: ServiceProvider) -> ServiceProvider:
        """Disables a Service Provider"""
        service_provider.status = ServiceProviderStatus.INACTIVE
        logger.info("Disabled Service Provider")
        return service_provider

    def create_service_provider(
        self,
        name: str,
        service_provider_type: ServiceProviderType,
        status: ServiceProviderStatus,
        primary_contact: PrimaryContact,
        name_count: int = 0,
    ) -> ServiceProvider:
        """Create a ServiceProvider.
        Requires name and type, status, and primary_contact
        """
        service_provider = ServiceProvider(
            uuid=str(uuid.uuid4()),
            name=name,
            service_provider_type=service_provider_type,
            status=status,
            primary_contact=primary_contact,
        )
        service_provider = self.set_name(service_provider, name, name_count)
        logger.info(f"Created Service Provider: \n{service_provider}")
        return service_provider

    def set_name(
        self, service_provider: ServiceProvider, name: str, name_count: int
    ) -> ServiceProvider:
        if name_count > 0:
            errors = {"general_fields": {"name": f"{name} is not unique"}}
            logger.error(f"Duplicate service provider name, {name} already exists")
            raise ServiceProviderNameDuplicate(message="name already exists", errors=errors)
        service_provider.name = name
        return service_provider

    def dump_service_provider_ders_to_csv(self, service_provider: ServiceProvider):
        ders = service_provider.ders
        header = [
            "ServiceProvider ID",
            "DER ID",
            "Name",
            "Der Type",
            "Nameplate Rating",
            "Rating Unit",
            "Resource Type",
        ]
        data = io.StringIO()
        cw = csv.writer(data)
        cw.writerow(header)
        for der in ders:
            cw.writerow(
                [
                    der.service_provider_id,
                    der.der_id,
                    der.name,
                    der.der_type.value,
                    der.nameplate_rating,
                    der.nameplate_rating_unit.value,
                    der.resource_category.value,
                ]
            )
        buf = io.BytesIO()
        buf.write(data.getvalue().encode("utf-8-sig"))
        buf.seek(0)
        buf.name = self._generate_csv_name(service_provider)
        return buf

    def _generate_csv_name(self, service_provider):
        return service_provider.name.strip() + " DER List.csv"


@dataclass
class GenericFields(DataClassJsonMixin):
    name: Optional[str] = None
    service_provider_type: Optional[ServiceProviderType] = None
    status: Optional[ServiceProviderStatus] = None


@dataclass
class CreateUpdateServiceProvider(DataClassJsonMixin):
    general_fields: GenericFields
    primary_contact: Optional[PrimaryContact] = None
    notification_contact: Optional[PrimaryContact] = None
    address: Optional[Address] = None


class ServiceProviderNameDuplicate(Error):
    pass
