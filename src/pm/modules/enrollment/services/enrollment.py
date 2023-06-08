from __future__ import annotations

import csv
import io
from typing import Optional, TypedDict

import pendulum

from pm.modules.enrollment.enums import (
    ContractStatus,
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.enrollment.models.enrollment import (
    Contract,
    DemandResponseDict,
    DynamicOperatingEnvelopesDict,
    EnrollmentRequest,
)
from pm.modules.progmgmt.models import Program
from pm.modules.serviceprovider.repository import ServiceProviderNotFound
from shared.enums import ProgramTypeEnum
from shared.exceptions import Error
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class EnrollmentService:
    def _validate_dynamic_operating_envelopes_for_doe_enrollment(
        self, enrollment_request_data: CreateUpdateEnrollmentRequestDict, program: Program
    ) -> None:
        if program.program_type is ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES:
            if "dynamic_operating_envelopes" not in enrollment_request_data:
                logger.error("Create Enrollment Request failed due to missing value")
                raise InvalidEnrollmentRequestArgs(
                    message=(
                        "Enrollment Request program type is "
                        "DYNAMIC OPERATING ENVELOPES but it is missing default limits"
                    )
                )
            check_fields = dict(
                default_limits_active_power_import_kw="Default Limits - Active Power Import (kW)",
                default_limits_active_power_export_kw="Default Limits - Active Power Export (kW)",
                default_limits_reactive_power_import_kw="Default Limits - Reactive Power Import (kW)",  # noqa E501
                default_limits_reactive_power_export_kw="Default Limits - Reactive Power Export (kW)",  # noqa E501
            )
            error_messages = [" should be provided", " should not be negative"]
            for key, value in check_fields.items():
                if (
                    key
                    not in enrollment_request_data["dynamic_operating_envelopes"]  # type: ignore
                ):
                    logger.error(
                        "Create Enrollment Request failed due to: " + value + error_messages[0]
                    )
                    raise InvalidEnrollmentRequestArgs(message=value + error_messages[0])
                if (
                    enrollment_request_data["dynamic_operating_envelopes"][key]  # type: ignore
                    is None
                ):
                    logger.error(
                        "Create Enrollment Request failed due to: " + value + error_messages[1]
                    )
                    raise InvalidEnrollmentRequestArgs(message=value + error_messages[1])

                if enrollment_request_data["dynamic_operating_envelopes"][key] < 0:  # type: ignore
                    logger.error(
                        "Create Enrollment Request failed due to: " + value + error_messages[1]
                    )
                    raise InvalidEnrollmentRequestArgs(message=value + error_messages[1])

    def _validate_demand_response_for_define_contractual_target_capacity_enrollment(
        self, enrollment_request_data: CreateUpdateEnrollmentRequestDict, program: Program
    ) -> None:
        if program.define_contractual_target_capacity:
            if "demand_response" not in enrollment_request_data:
                logger.error("Create Enrollment Request failed due to missing value")
                raise InvalidEnrollmentRequestArgs(
                    message=(
                        "Enrollment Request program has define_contractual_target_capacity "
                        "set to True but it is missing contractual target capacity"
                    )
                )

    def _validate_svc_provider_enrollment(
        self, enrollment_request_data: CreateUpdateEnrollmentRequestDict
    ) -> None:
        service_provider_id = enrollment_request_data["general_fields"].get("service_provider_id")
        try:
            if not isinstance(service_provider_id, int):
                raise ServiceProviderNotFound(message="Service provider id should be an integer")
        except ServiceProviderNotFound as e:
            raise InvalidEnrollmentRequestArgs(message=e.message)

    def _validate_required_fields_enrollment(
        self, enrollment_request_data: CreateUpdateEnrollmentRequestDict
    ) -> None:
        service_provider_id = enrollment_request_data["general_fields"].get("service_provider_id")
        der_id = enrollment_request_data["general_fields"].get("der_id")
        if not service_provider_id or not der_id:
            logger.error("Create Enrollment Request failed due to missing value")
            raise InvalidEnrollmentRequestArgs(
                message=(
                    "Enrollment Request is missing one of the value: program_id, "
                    "enrollment_program_type, service_provider_id, der_id"
                )
            )

    def validate_enrollment_request(
        self, enrollment_request_data: CreateUpdateEnrollmentRequestDict, program: Program
    ) -> CreateUpdateEnrollmentRequestDict:
        self._validate_required_fields_enrollment(enrollment_request_data)
        self._validate_svc_provider_enrollment(enrollment_request_data)
        self._validate_dynamic_operating_envelopes_for_doe_enrollment(
            enrollment_request_data, program
        )
        self._validate_demand_response_for_define_contractual_target_capacity_enrollment(
            enrollment_request_data, program
        )
        return enrollment_request_data

    def _set_enrollment_specific_fields(
        self,
        enrollment_request: EnrollmentRequest,
        data: CreateUpdateEnrollmentRequestDict,
        program: Program,
    ) -> EnrollmentRequest:
        if program.program_type == ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES:
            dynamic_operating_envelopes = data.get("dynamic_operating_envelopes")
            if dynamic_operating_envelopes is not None:
                enrollment_request.dynamic_operating_envelopes = dynamic_operating_envelopes
        elif program.define_contractual_target_capacity:
            demand_response = data.get("demand_response")
            if demand_response is not None:
                enrollment_request.demand_response = demand_response
        return enrollment_request

    def _set_shared_fields(
        self, enrollment_request: EnrollmentRequest, payload: CreateUpdateEnrollmentRequestDict
    ) -> EnrollmentRequest:
        general_fields = payload.get("general_fields", {})

        program_id = general_fields.get("program_id")
        if program_id is not None:
            enrollment_request.program_id = program_id

        service_provider_id = general_fields.get("service_provider_id")
        if service_provider_id is not None:
            enrollment_request.service_provider_id = service_provider_id

        der_id = general_fields.get("der_id")
        if der_id is not None:
            enrollment_request.der_id = der_id

        enrollment_status = general_fields.get("enrollment_status")
        if enrollment_status is not None:
            enrollment_request.enrollment_status = enrollment_status

        rejection_reason = general_fields.get("rejection_reason")
        if rejection_reason is not None:
            enrollment_request.rejection_reason = rejection_reason

        return enrollment_request

    def set_enrollment_request_fields(
        self,
        enrollment_request: EnrollmentRequest,
        data: CreateUpdateEnrollmentRequestDict,
        program: Program,
    ) -> EnrollmentRequest:
        """Saves a user's enrollment
        Creates a EnrollmentSaved event
        """
        self._set_shared_fields(enrollment_request, data)
        self._set_enrollment_specific_fields(enrollment_request, data, program)
        logger.info("Saved Enrollment")
        return enrollment_request

    def reject_enrollment_request(
        self, enrollment_request: EnrollmentRequest, reason: EnrollmentRejectionReason
    ) -> EnrollmentRequest:
        """Rejects a user's enrollment
        Creates a EnrollmentRejected event
        """
        enrollment_request.enrollment_status = EnrollmentRequestStatus.REJECTED
        enrollment_request.rejection_reason = reason
        logger.info(f"Rejected Enrollment Request: {reason}")
        return enrollment_request

    def accept_enrollment_request(self, enrollment_request: EnrollmentRequest) -> EnrollmentRequest:
        """Accepts a user's enrollment
        Creates a EnrollmentAccepted event
        """
        enrollment_request.enrollment_status = EnrollmentRequestStatus.ACCEPTED
        logger.info("Accepted Enrollment Request")
        return enrollment_request

    def create_enrollment_request(
        self,
        program_id: int,
        service_provider_id: int,
        der_id: str,
    ) -> EnrollmentRequest:
        """Create a Enrollment"""
        enrollment_request = EnrollmentRequest(
            program_id=program_id,
            service_provider_id=service_provider_id,
            der_id=der_id,
            enrollment_status=EnrollmentRequestStatus.PENDING,
        )

        logger.info(f"Created Enrollment Request \n{enrollment_request}")
        return enrollment_request

    def create_enrollment_allowed(self, program: Program, existing_contract: Optional[Contract]):
        if program.end_date and pendulum.now() > program.end_date:
            raise EnrollmentRequestNotAllowed(
                message="Enrollment Request is for program that has ended"
            )
        if existing_contract:
            if existing_contract.contract_status != ContractStatus.SYSTEM_CANCELLED:
                raise EnrollmentRequestNotAllowed(
                    message="Contract already exists for this program, service provider, and der"
                )

    def create_enrollment_report(self, enrollment_requests: list[EnrollmentRequest]) -> io.BytesIO:
        output = io.StringIO()

        writer = csv.DictWriter(
            output,
            EnrollmentRequest.get_report_headers(),
        )
        writer.writeheader()
        for enrollment_request in enrollment_requests:
            writer.writerow(enrollment_request.get_report_row())
        output.seek(0)
        return io.BytesIO(output.getvalue().encode(encoding="utf-8"))


class InvalidEnrollmentRequestArgs(Error):
    pass


class EnrollmentRequestNotAllowed(Error):
    pass


class EnrollmentRequestGenericFieldsDict(TypedDict):
    program_id: int
    service_provider_id: int
    der_id: str
    enrollment_status: Optional[EnrollmentRequestStatus]
    rejection_reason: Optional[EnrollmentRejectionReason]


class CreateUpdateEnrollmentRequestDict(TypedDict):
    general_fields: EnrollmentRequestGenericFieldsDict
    dynamic_operating_envelopes: Optional[DynamicOperatingEnvelopesDict]
    demand_response: Optional[DemandResponseDict]
