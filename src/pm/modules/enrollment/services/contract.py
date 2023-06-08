from __future__ import annotations

from typing import TypedDict

from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.modules.enrollment.models.enrollment import (
    Contract,
    DemandResponseDict,
    DynamicOperatingEnvelopesDict,
    EnrollmentRequest,
)
from pm.modules.progmgmt.models import Program
from shared.exceptions import Error
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ContractService:
    def validate_contract_creation_data(
        self, contract_data: CreateUpdateContractDict
    ) -> tuple[ContractStatus, ContractType, int, str, int, int]:
        (
            contract_status,
            contract_type,
            enrollment_request_id,
            der_id,
            program_id,
            service_provider_id,
        ) = self._validate_required_fields_contract(contract_data)
        self._validate_dynamic_operating_envelopes_for_doe_contract(contract_data)
        return (
            contract_status,
            contract_type,
            enrollment_request_id,
            der_id,
            program_id,
            service_provider_id,
        )

    def _validate_required_fields_contract(
        self, contract_data: CreateUpdateContractDict
    ) -> tuple[ContractStatus, ContractType, int, str, int, int]:
        contract_status = contract_data.get("contract_status")
        contract_type = contract_data.get("contract_type")
        enrollment_request_id = contract_data.get("enrollment_request_id")
        der_id = contract_data.get("der_id")
        program_id = contract_data.get("program_id")
        service_provider_id = contract_data.get("service_provider_id")
        if (
            not contract_status
            or not contract_type
            or not enrollment_request_id
            or not der_id
            or not program_id
            or not service_provider_id
        ):
            logger.error("Create Contract failed due to missing value")
            raise InvalidContractArgs(
                message=(
                    "Contract Create is missing one of the value: contract_status, "
                    "contract_type, enrollment_request_id, der_id, program_id, service_provider_id"
                )
            )
        return (
            contract_status,
            contract_type,
            enrollment_request_id,
            der_id,
            program_id,
            service_provider_id,
        )

    def _validate_dynamic_operating_envelopes_for_doe_contract(
        self, contract_data: CreateUpdateContractDict
    ) -> None:
        contract_doe = contract_data.get("dynamic_operating_envelopes")

        check_fields = dict(
            default_limits_active_power_import_kw="Default Limits - Active Power Import (kW)",
            default_limits_active_power_export_kw="Default Limits - Active Power Export (kW)",
            default_limits_reactive_power_import_kw="Default Limits - Reactive Power Import (kW)",
            default_limits_reactive_power_export_kw="Default Limits - Reactive Power Export (kW)",
        )
        error_messages = [" should be provided", " should not be negative"]

        if contract_doe is not None:
            for key, value in check_fields.items():
                if key not in contract_doe:  # type: ignore
                    logger.error("Contract Create failed due to: " + value + error_messages[0])
                    raise InvalidContractArgs(message=value + error_messages[0])
                if contract_doe[key] is None:  # type: ignore
                    logger.error("Contract Create failed due to:" + value + error_messages[1])
                    raise InvalidContractArgs(message=value + error_messages[1])
                if contract_doe[key] < 0:  # type: ignore
                    logger.error("Contract Create failed due to:" + value + error_messages[1])
                    raise InvalidContractArgs(message=value + error_messages[1])

    def create_contract_from_enrollment_request(
        self, enrollment_request: EnrollmentRequest, program: Program
    ) -> Contract:
        contract_status = ContractStatus.map_program_status_to_contract_status(
            program_status=program.status
        )
        if not contract_status:
            logger.error(
                "Contract Create failed due to: "
                + "Cannot determine the contract status from the program status"
            )
            raise InvalidContractArgs(
                message="Contract Create failed due to: "
                + "Cannot determine the contract status from the program status"
            )
        contract = self.create_contract(
            contract_status=contract_status,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request.id,
            program_id=enrollment_request.program_id,
            der_id=enrollment_request.der_id,
            service_provider_id=enrollment_request.service_provider_id,  # type: ignore
        )
        data = CreateUpdateContractDict(  # type: ignore
            dynamic_operating_envelopes=enrollment_request.dynamic_operating_envelopes,
            demand_response=enrollment_request.demand_response,
        )
        return self.set_contract_fields(contract, data)

    def create_contract(
        self,
        contract_status: ContractStatus,
        contract_type: ContractType,
        enrollment_request_id: int,
        program_id: int,
        der_id: str,
        service_provider_id: int,
    ) -> Contract:
        """Create a Contract"""
        contract = Contract(
            contract_status=contract_status,
            contract_type=contract_type,
            enrollment_request_id=enrollment_request_id,
            program_id=program_id,
            der_id=der_id,
            service_provider_id=service_provider_id,
        )
        logger.info(f"Created Contract \n{contract}")
        return contract

    def set_contract_fields(self, contract: Contract, data: CreateUpdateContractDict) -> Contract:
        """Saves a contract"""
        self._validate_dynamic_operating_envelopes_for_doe_contract(data)
        contract = self._update_contract_fields(contract, data)
        logger.info("Saved Contract")
        return contract

    def _update_contract_fields(
        self, contract: Contract, data: CreateUpdateContractDict
    ) -> Contract:
        """Saves a contract"""
        if self._can_contract_be_updated(contract=contract):
            dynamic_operating_envelopes = data.get("dynamic_operating_envelopes")
            if dynamic_operating_envelopes is not None:
                contract.dynamic_operating_envelopes = dynamic_operating_envelopes

            demand_response = data.get("demand_response")
            if demand_response is not None:
                contract.demand_response = demand_response
            return contract
        else:
            raise InvalidContractArgs(
                message="Contract cannot be updated as it is either cancelled or expired"
            )

    def _can_contract_be_updated(self, contract: Contract) -> bool:
        is_cancelled = any(
            [
                ContractStatus.is_user_cancelled(contract.contract_status),
                ContractStatus.is_system_cancelled(contract.contract_status),
            ]
        )
        is_expired = ContractStatus.is_expired(contract.contract_status)
        return not (any([is_cancelled, is_expired]))

    def update_contract_status(
        self, contract: Contract, contract_status: ContractStatus
    ) -> Contract:
        contract.contract_status = contract_status
        logger.info("Updated Contract Status")
        return contract

    def find_status_after_undo_cancellation(self, program: Program) -> ContractStatus | None:
        return ContractStatus.map_program_status_to_contract_status(program.status)

    def check_undo_cancel_contract_request(self, contract: Contract, program: Program):
        is_cancelled = ContractStatus.is_user_cancelled(contract.contract_status)
        if not is_cancelled:
            e: str = (
                "The contract cannot be re-activated as "
                + "previously it has not been cancelled by user"
            )
            logger.error(e)
            raise InvalidUndoCancellation(e)
        else:
            status_post_undo_cancel = self.find_status_after_undo_cancellation(program)
            if status_post_undo_cancel:
                return
            else:
                e = (
                    "The contract cannot be re-activated as "
                    + "the status of the contract cannot be mapped to the program's status"
                )
                logger.error(e)
                raise InvalidProgramStatusForContract(e)

    def check_cancel_contract_request(self, contract: Contract) -> bool:
        if (
            contract.contract_status is ContractStatus.ACTIVE
            or contract.contract_status is ContractStatus.ACCEPTED
        ):
            return True
        else:
            return False

    def system_cancel_contract(self, contract: Contract) -> Contract:
        """
        System Cancellation of Contract. Cannot do undo cancellation on the contract
        """
        contract = self.update_contract_status(contract, ContractStatus.SYSTEM_CANCELLED)
        return contract


class InvalidContractArgs(Error):
    pass


class InvalidProgramStatusForContract(Error):
    pass


class InvalidUndoCancellation(Error):
    pass


class CreateUpdateContractDict(TypedDict):
    contract_status: ContractStatus
    contract_type: ContractType
    enrollment_request_id: int
    program_id: int
    der_id: str
    service_provider_id: int
    dynamic_operating_envelopes: DynamicOperatingEnvelopesDict
    demand_response: DemandResponseDict
