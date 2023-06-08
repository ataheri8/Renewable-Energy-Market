from pm.modules.enrollment.contract_repository import ContractRepository
from pm.modules.enrollment.enums import ContractStatus
from pm.modules.enrollment.models.enrollment import Contract
from pm.modules.enrollment.repository import EnrollmentRequestRepository
from pm.modules.enrollment.services.contract import (
    ContractService,
    CreateUpdateContractDict,
    InvalidContractArgs,
    InvalidProgramStatusForContract,
)
from pm.modules.progmgmt.enums import ProgramStatus
from pm.modules.progmgmt.repository import ProgramRepository
from shared.repository import UOW
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ContractUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.contract_repository = ContractRepository(self.session)
        self.program_repository = ProgramRepository(self.session)
        self.enrollment_request_repository = EnrollmentRequestRepository(self.session)
        return self


class ContractController:
    def __init__(self):
        self.contract_service = ContractService()
        self.unit_of_work = ContractUOW()

    def create_contract(self, contract_datas: list[CreateUpdateContractDict]) -> list[dict]:
        contract_ids = []
        with self.unit_of_work as uow:
            for contract_data in contract_datas:
                try:
                    (
                        contract_status,
                        contract_type,
                        enrollment_request_id,
                        der_id,
                        program_id,
                        service_provider_id,
                    ) = self.contract_service.validate_contract_creation_data(contract_data)

                except InvalidContractArgs as e:
                    contract_ids.append(
                        {
                            "id": "",
                            "status": "NOT_CREATED",
                            "message": e.message,
                            "data": contract_data,
                        }
                    )
                    continue
                contract = self.contract_service.create_contract(
                    contract_status=contract_status,
                    contract_type=contract_type,
                    enrollment_request_id=enrollment_request_id,
                    der_id=der_id,
                    program_id=program_id,
                    service_provider_id=service_provider_id,
                )
                self.contract_service.set_contract_fields(contract, contract_data)
                contract_id = uow.contract_repository.save_create_contract(contract)
                contract_ids.append(
                    {
                        "id": contract_id,
                        "status": "CREATED",
                        "message": "",
                        "data": contract_data,
                    }
                )
            uow.commit()
        return contract_ids

    def update_contract(self, contract_id: int, data: CreateUpdateContractDict) -> int:
        with self.unit_of_work as uow:
            contract = uow.contract_repository.get_contract_or_raise(contract_id)
            contract = self.contract_service.set_contract_fields(contract, data)
            contract_id = uow.contract_repository.save_update_contract(contract)
            uow.commit()
            return contract_id

    def cancel_contract(self, contract_id: int) -> bool:
        with self.unit_of_work as uow:
            contract = uow.contract_repository.get_contract_or_raise(contract_id)
            if self.contract_service.check_cancel_contract_request(contract):
                contract = self.contract_service.update_contract_status(
                    contract, contract_status=ContractStatus.USER_CANCELLED
                )
                uow.contract_repository.save_delete_contract(contract)
                uow.commit()
                return True
            return False

    def cancel_contracts_by_der_id(self, der_id: str):
        with self.unit_of_work as uow:
            contracts = uow.contract_repository.get_unexpired_contracts_by_der_id(der_id)
            for contract in contracts:
                contract = self.contract_service.system_cancel_contract(contract)
                uow.contract_repository.save_delete_contract(contract)
            uow.commit()

    def undo_cancel_contract(self, contract_id: int):
        with self.unit_of_work as uow:
            contract = uow.contract_repository.get_contract_or_raise(contract_id)
            program = uow.program_repository.get_program_or_raise(
                contract.program_id, eager_load_relationships=False
            )
            self.contract_service.check_undo_cancel_contract_request(contract, program)

            if program.status == ProgramStatus.ARCHIVED:
                e: str = "Cannot re-activate the contract as the program has expired"
                logger.error(e)
                raise InvalidProgramStatusForContract(e)
            post_contract_status = self.contract_service.find_status_after_undo_cancellation(
                program
            )
            contract = self.contract_service.update_contract_status(
                contract, contract_status=post_contract_status  # type: ignore
            )
            uow.contract_repository.save_undo_delete_contract(contract)
            uow.commit()

    def get_all_contracts(self) -> list[Contract]:
        with self.unit_of_work as uow:
            return uow.contract_repository.get_all(eager_load=True)

    def get_contract(self, contract_id: int, eager_load=True) -> Contract:
        with self.unit_of_work as uow:
            return uow.contract_repository.get_contract_or_raise(contract_id, eager_load)

    def activate_contracts(self):
        """Activate all contracts that have associated program activated."""
        with self.unit_of_work as uow:
            contracts = uow.contract_repository.get_contracts_to_activate()
            for contract in contracts:
                contract = self.contract_service.update_contract_status(
                    contract, ContractStatus.ACTIVE
                )
                uow.contract_repository.save_update_contract(contract)
            uow.commit()

    def expire_contracts_archived_programs(self):
        """Expire all contracts that are active or accepted and the associated program is set to
        expire."""
        with self.unit_of_work as uow:
            contracts = uow.contract_repository.get_contracts_to_expire()
            for contract in contracts:
                contract = self.contract_service.update_contract_status(
                    contract, ContractStatus.EXPIRED
                )
                uow.contract_repository.save_update_contract(contract)
            uow.commit()
