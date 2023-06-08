import io
from typing import Optional

from werkzeug.datastructures import FileStorage

from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.derinfo.repository import DerInfoRepository, DerNotFound
from pm.modules.enrollment.contract_repository import ContractRepository
from pm.modules.enrollment.enums import EnrollmentCRUDStatus, EnrollmentRequestStatus
from pm.modules.enrollment.models.enrollment import EnrollmentRequest
from pm.modules.enrollment.repository import EnrollmentRequestRepository
from pm.modules.enrollment.services.contract import ContractService
from pm.modules.enrollment.services.eligibility.eligibility import EligibilityService
from pm.modules.enrollment.services.enrollment import (
    CreateUpdateEnrollmentRequestDict,
    EnrollmentRequestNotAllowed,
    EnrollmentService,
    InvalidEnrollmentRequestArgs,
)
from pm.modules.progmgmt.enums import ProgramStatus
from pm.modules.progmgmt.models import Program
from pm.modules.progmgmt.repository import ProgramNotFound, ProgramRepository
from pm.modules.serviceprovider.models import ServiceProvider
from pm.modules.serviceprovider.repository import (
    ServiceProviderNotFound,
    ServiceProviderRepository,
)
from shared.minio_manager import MinioManager
from shared.repository import UOW
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class EnrollmentUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.contract_repository = ContractRepository(self.session)
        self.program_repository = ProgramRepository(self.session)
        self.enrollment_request_repository = EnrollmentRequestRepository(self.session)
        self.der_info_repository = DerInfoRepository(self.session)
        self.service_provider_repository = ServiceProviderRepository(self.session)
        return self


class EnrollmentController:
    def __init__(self):
        self.unit_of_work = EnrollmentUOW()
        self.enrollment_service = EnrollmentService()
        self.eligibility_service = EligibilityService()
        self.contract_service = ContractService()
        self.minio_manager = MinioManager()

    def create_enrollment_requests(
        self, enrollment_requests_data: list[CreateUpdateEnrollmentRequestDict]
    ) -> list[dict]:
        enrollment_request_ids: list[dict] = []
        for enrollment_request_data in enrollment_requests_data:
            enrollment_request_id = self.create_enrollment_request(enrollment_request_data)
            enrollment_request_ids.append(enrollment_request_id)

        return enrollment_request_ids

    def create_enrollment_request(
        self,
        enrollment_request_data: CreateUpdateEnrollmentRequestDict,
    ) -> dict:
        with self.unit_of_work as uow:
            try:
                program, service_provider, der = self._validate_extract_enrollment_request_fields(
                    enrollment_request_data,
                    uow,
                )
            except (
                InvalidEnrollmentRequestArgs,
                EnrollmentRequestNotAllowed,
                ProgramNotFound,
                ServiceProviderNotFound,
                DerNotFound,
            ) as e:
                return {
                    "id": None,
                    "status": EnrollmentCRUDStatus.NOT_CREATED,
                    "message": e.message,
                    "data": enrollment_request_data,
                }

            # Create Enrollment Request object and set fields
            enrollment_request = self.enrollment_service.create_enrollment_request(
                program_id=program.id,
                service_provider_id=service_provider.id,
                der_id=der.der_id,
            )
            self.enrollment_service.set_enrollment_request_fields(
                enrollment_request, enrollment_request_data, program
            )

            # Run Eligibility Check and save Enrollment Request to database
            status, reason = self.eligibility_service.eligibility_check(
                program, der, enrollment_request
            )
            if status == EnrollmentRequestStatus.ACCEPTED:
                self.enrollment_service.accept_enrollment_request(enrollment_request)
            elif status == EnrollmentRequestStatus.REJECTED and reason:
                self.enrollment_service.reject_enrollment_request(enrollment_request, reason)

            enrollment_request_id = uow.enrollment_request_repository.save(enrollment_request)

            # Create Contract object and save to database if eligibility check was successful
            if status == EnrollmentRequestStatus.ACCEPTED:
                enrollment_request = (
                    uow.enrollment_request_repository.get_enrollment_request_or_raise(
                        enrollment_request_id
                    )
                )
                contract = self.contract_service.create_contract_from_enrollment_request(
                    enrollment_request, program
                )
                uow.contract_repository.save_create_contract(contract)
            uow.commit()
            return {
                "id": enrollment_request_id,
                "status": EnrollmentCRUDStatus.CREATED,
                "message": "",
                "data": enrollment_request_data,
            }

    def get_all_enrollment_requests(self) -> list[EnrollmentRequest]:
        with self.unit_of_work as uow:
            return uow.enrollment_request_repository.get_all()

    def get_enrollment_request(self, enrollment_request_id: int) -> Optional[EnrollmentRequest]:
        with self.unit_of_work as uow:
            return uow.enrollment_request_repository.get_enrollment_request_or_raise(
                enrollment_request_id
            )

    def enrollment_request_upload(
        self,
        program_id: int,
        file: FileStorage,
        tags=None,
    ):
        with self.unit_of_work as uow:
            uow.program_repository.get_program_or_raise(program_id)
            my_tags: dict = {} or tags
            more_tags = {
                **my_tags,
                "program_id": str(program_id),
                "FILE_TYPE": "EnrollmentRequest",
            }
            self.minio_manager.upload_csv_to_minio(file, more_tags)

    def get_enrollment_report(self, program_id: int) -> io.BytesIO:
        with self.unit_of_work as uow:
            program = uow.program_repository.get_program_or_raise(program_id)
            enrollment_requests = uow.enrollment_request_repository.get_enrollments_for_report(
                program.id
            )
            return self.enrollment_service.create_enrollment_report(enrollment_requests)

    def _validate_extract_enrollment_request_fields(
        self,
        enrollment_request_data: CreateUpdateEnrollmentRequestDict,
        uow: EnrollmentUOW,
    ) -> tuple[Program, ServiceProvider, DerInfo]:
        program_id, program = self.is_non_archived_program_existing(enrollment_request_data, uow)
        enrollment_request_data = self.enrollment_service.validate_enrollment_request(
            enrollment_request_data, program
        )
        service_provider_id, service_provider = self.is_service_provider_existing(
            enrollment_request_data, uow
        )
        der_id, der = self.is_der_existing(enrollment_request_data, uow)
        self.is_contract_already_existing(uow, program_id, program, service_provider_id, der_id)
        return program, service_provider, der

    def is_non_archived_program_existing(self, enrollment_request_data, uow):
        program_id = enrollment_request_data["general_fields"].get("program_id")
        if not program_id:
            logger.error("Create Enrollment Request failed due to missing program_id")
            raise InvalidEnrollmentRequestArgs(message="Enrollment Request is missing program_id")
        program = uow.program_repository.get_program_or_raise(
            program_id, eager_load_relationships=False
        )
        if program.status == ProgramStatus.ARCHIVED:
            logger.error("Create Enrollment Request failed due to expired program_id")
            raise InvalidEnrollmentRequestArgs(
                message="Enrollment Request is having expired program_id"
            )

        return program_id, program

    def is_service_provider_existing(self, enrollment_request_data, uow):
        service_provider_id = enrollment_request_data["general_fields"]["service_provider_id"]
        service_provider = uow.service_provider_repository.get_service_provider_or_raise(
            service_provider_id, include_inactive=False
        )

        return service_provider_id, service_provider

    def is_contract_already_existing(self, uow, program_id, program, service_provider_id, der_id):
        existing_contract = uow.contract_repository.get_contract_by_unique_constraint(
            program_id, service_provider_id, der_id
        )
        self.enrollment_service.create_enrollment_allowed(program, existing_contract)

    def is_der_existing(self, enrollment_request_data, uow):
        der_id = enrollment_request_data["general_fields"]["der_id"]
        der = uow.der_info_repository.get_der_or_raise_exception(der_id=der_id)
        return der_id, der
