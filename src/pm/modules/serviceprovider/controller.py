from __future__ import annotations

from typing import Optional, TypedDict

from werkzeug.datastructures import FileStorage

from pm.modules.enrollment.contract_controller import ContractController
from pm.modules.serviceprovider.enums import ServiceProviderStatus
from pm.modules.serviceprovider.models.service_provider import ServiceProvider
from pm.modules.serviceprovider.repository import (
    ServiceProviderNoDerAssociationFound,
    ServiceProviderNotFound,
    ServiceProviderRepository,
)
from pm.modules.serviceprovider.services.service_provider import (
    CreateUpdateServiceProvider,
    ServiceProviderService,
)
from shared.exceptions import Error
from shared.minio_manager import MinioManager
from shared.repository import UOW
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ServiceProviderUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.repository = ServiceProviderRepository(self.session)
        return self


class ServiceProviderController:
    def __init__(self):
        self.unit_of_work = ServiceProviderUOW()
        self.service_provider_service = ServiceProviderService()
        self.minio_manager = MinioManager()
        self.contract_controller = ContractController()

    def create_service_provider(self, payload: CreateUpdateServiceProvider) -> int:
        with self.unit_of_work as uow:
            gen_fields = payload.general_fields
            if (
                not gen_fields.name
                or not gen_fields.service_provider_type
                or not gen_fields.status
                or not payload.primary_contact
            ):
                logger.error("Unable to create service provider due to missing argument")
                raise InvalidServiceProviderArgs(
                    message="It is required to provide Service Provider name, type,"
                    + "status, and primary contact"
                )
            name_count = uow.repository.count_by_name(gen_fields.name)
            service_provider = self.service_provider_service.create_service_provider(
                name=gen_fields.name,
                service_provider_type=gen_fields.service_provider_type,
                status=gen_fields.status,
                primary_contact=payload.primary_contact,
                name_count=name_count,
            )
            self.service_provider_service.set_service_provider_fields(service_provider, payload)
            id = uow.repository.save(service_provider)
            uow.commit()
            return id

    def delete_service_provider(self, service_provider_id: int) -> int:
        with self.unit_of_work as uow:
            service_provider = uow.repository.get_service_provider_or_raise(service_provider_id)
            ders = service_provider.ders
        for der in ders:
            self.contract_controller.cancel_contracts_by_der_id(der.der_id)
        with self.unit_of_work as uow:
            self.service_provider_service.delete_service_provider(service_provider)
            id = uow.repository.save(service_provider)
            uow.commit()
            return id

    def enable_service_provider(self, service_provider_id: int) -> int:
        with self.unit_of_work as uow:
            service_provider = uow.repository.get_service_provider_or_raise(service_provider_id)
            if service_provider.status != ServiceProviderStatus.ACTIVE:
                self.service_provider_service.enable_service_provider(service_provider)
                id = uow.repository.save(service_provider)
                uow.commit()
                return id
            else:
                raise ServiceProviderNotFound(
                    errors={"error": "Not Allowed"},
                    message="Service provider with id "
                    + str(service_provider_id)
                    + " is already enabled",
                )

    def disable_service_provider(self, service_provider_id: int) -> int:
        with self.unit_of_work as uow:
            service_provider = uow.repository.get_service_provider_or_raise(service_provider_id)
            ders = service_provider.ders
        if service_provider.status != ServiceProviderStatus.INACTIVE:
            for der in ders:
                self.contract_controller.cancel_contracts_by_der_id(der.der_id)
            with self.unit_of_work as uow:
                self.service_provider_service.disable_service_provider(service_provider)
                id = uow.repository.save(service_provider)
                uow.commit()
                return id
        else:
            raise ServiceProviderNotFound(
                errors={"error": "Not Allowed"},
                message="Service provider with id "
                + str(service_provider_id)
                + " is already disabled",
            )

    def update_service_provider(
        self, service_provider_id: int, payload: CreateUpdateServiceProvider
    ) -> int:
        payload.general_fields.status = None
        with self.unit_of_work as uow:
            service_provider = uow.repository.get_service_provider_or_raise(service_provider_id)
            name = payload.general_fields.name
            if name and name != service_provider.name:
                name_count = uow.repository.count_by_name(name)
                self.service_provider_service.set_name(service_provider, name, name_count)
            self.service_provider_service.set_service_provider_fields(service_provider, payload)
            id = uow.repository.save(service_provider)
            uow.commit()
            return id

    def associate_ders(self, service_provider_id: int, der_list: list[DerList]) -> list[dict]:
        ders_uuid = []
        ders_output = []
        with self.unit_of_work as uow:
            uow.repository.get_service_provider_or_raise(
                service_provider_id, include_inactive=False
            )
        with self.unit_of_work as uow:
            for der in der_list:
                incorrect_data = False
                if ("der_id" in der) and (str(der["der_id"])):
                    if der["der_id"] in ders_uuid:
                        ders_output.append(
                            {
                                "der_id": der["der_id"],
                                "outcome": "could not associated to service provider with id "
                                + str(service_provider_id),
                                "reason": "Duplicate der_id",
                                "status_code": 1,
                            }
                        )
                        continue
                    existing_der = uow.repository.get_der_without_serviceprovider(
                        der_id=der["der_id"]
                    )
                    ders_uuid.append(der["der_id"])
                else:
                    existing_der = None
                    incorrect_data = True
                    ders_output.append(
                        {
                            "der_id": "",
                            "outcome": "could not associated to service provider with id "
                            + str(service_provider_id),
                            "reason": "Either incorrect format, values or missing der_id",
                            "status_code": 2,
                        }
                    )

                if not incorrect_data:
                    if existing_der is not None:
                        uow.repository.update_der(service_provider_id, der["der_id"])
                        ders_output.append(
                            {
                                "der_id": der["der_id"],
                                "outcome": "Associated to service provider with id "
                                + str(service_provider_id),
                                "reason": "",
                                "status_code": 3,
                            }
                        )
                    else:
                        ders_output.append(
                            {
                                "der_id": der["der_id"],
                                "outcome": "could not associated to service provider with id "
                                + str(service_provider_id),
                                "reason": "No DER found with der_id "
                                + str(der["der_id"])
                                + " or it is already associated with a different service provider.",
                                "status_code": 4,
                            }
                        )
            uow.commit()
        return ders_output

    def associate_ders_file_upload(
        self, service_provider_id: int, file: FileStorage, tags: dict | None = None
    ):
        with self.unit_of_work as uow:
            tags = tags or {}
            uow.repository.get_service_provider_or_raise(
                service_provider_id, include_inactive=False
            )
            tags = {
                **tags,
                "service_provider_id": str(service_provider_id),
                "FILE_TYPE": "ServiceProviderDERAssociation",
            }
            self.minio_manager.upload_csv_to_minio(file, tags)

    def service_providers_file_upload(self, file: FileStorage, tags: dict | None = None):
        tags = tags or {}
        tags = {
            **tags,
            "FILE_TYPE": "ServiceProvider",
        }
        self.minio_manager.upload_csv_to_minio(file, tags)

    def delete_der_service_provider(self, service_provider_id: int, der_id: int):
        with self.unit_of_work as uow:
            uow.repository.get_service_provider_or_raise(service_provider_id)
            der = uow.repository.get_der_or_raise(service_provider_id, der_id)
        self.contract_controller.cancel_contracts_by_der_id(der.der_id)
        with self.unit_of_work as uow:
            uow.repository.remove_service_provider(service_provider_id, der.id)
            uow.commit()

    def get_all_serviceproviders(self) -> list[ServiceProvider]:
        with self.unit_of_work as uow:
            return uow.repository.get_all(load_ders=True)

    def get_serviceprovider(self, service_provider_id: int) -> Optional[ServiceProvider]:
        with self.unit_of_work as uow:
            return uow.repository.get_service_provider_or_raise(service_provider_id, load_ders=True)

    def download_service_provider_data(self, service_provider_id: int):
        with self.unit_of_work as uow:
            service_provider: ServiceProvider = uow.repository.get_service_provider_or_raise(
                service_provider_id, load_ders=True
            )
            if len(service_provider.ders) == 0:
                logger.error(
                    "no DERs are associated with service provider id " + str(service_provider_id)
                )
                raise ServiceProviderNoDerAssociationFound(
                    message="no DERs are associated with service provider id "
                    + str(service_provider_id)
                )
            file = self.service_provider_service.dump_service_provider_ders_to_csv(service_provider)
            return file


class DerList(TypedDict):
    der_id: str


class InvalidServiceProviderArgs(Error):
    pass
