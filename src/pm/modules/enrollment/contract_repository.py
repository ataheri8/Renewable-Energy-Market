from typing import Optional, Sequence

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import joinedload

from pm.modules.enrollment.enums import ContractKafkaOperation, ContractStatus
from pm.modules.enrollment.models.enrollment import Contract, EnrollmentRequest
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.progmgmt.enums import ProgramStatus
from pm.modules.progmgmt.models.program import Program
from pm.topics import ContractMessage
from shared.exceptions import Error
from shared.repository import SQLRepository


class ContractRepository(SQLRepository):
    def _add_jointload_in_query(self, stmt: Select, eager_load: bool) -> Select:
        if eager_load:
            stmt = stmt.options(
                joinedload(Contract.der),
                joinedload(Contract.service_provider),
                joinedload(Contract.program),
            )
        return stmt

    def get_all(self, eager_load=False) -> Sequence[Contract]:
        stmt = select(Contract).order_by(Contract.id)
        stmt = self._add_jointload_in_query(stmt, eager_load)
        return self.session.execute(stmt).unique().scalars().all()

    def get(self, contract_id: int, eager_load=False) -> Optional[Contract]:
        """Gets the contract"""
        stmt = select(Contract).where(Contract.id == contract_id)
        stmt = self._add_jointload_in_query(stmt, eager_load)
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_contract_or_raise(self, contract_id: int, eager_load=False) -> Contract:
        """Gets the contract.
        Raises an error if contract is not found
        """
        contract = self.get(contract_id, eager_load)
        if not contract:
            raise ContractNotFound(
                errors={"error": "Not Found"},
                message=f"Contract with id {contract_id} is not found",
            )
        return contract

    def save_create_contract(self, contract: Contract) -> int:
        return self.save_contract(contract, operation=ContractKafkaOperation.CREATED)

    def save_update_contract(self, contract: Contract) -> int:
        return self.save_contract(contract, operation=ContractKafkaOperation.UPDATED)

    def save_delete_contract(self, contract: Contract) -> int:
        return self.save_contract(contract, operation=ContractKafkaOperation.DELETED)

    def save_undo_delete_contract(self, contract: Contract) -> int:
        return self.save_contract(contract, operation=ContractKafkaOperation.REACTIVATED)

    def save_contract(self, contract: Contract, operation: ContractKafkaOperation) -> int:
        """Saves a contract and publishes on pm.contract"""
        _id: int
        self.session.add(contract)
        self.session.flush()
        ContractMessage.add_to_outbox(
            self.session,
            contract.to_dict(include_relationships=False),
            {"operation": operation.value},
        )  # type: ignore
        _id = contract.id
        return _id

    def get_contracts_by_program_id(self, program_id: int) -> Sequence[Contract]:
        stmt = select(Contract).where(Contract.program_id == program_id)
        return self.session.execute(stmt).unique().scalars().all()

    def get_contracts_by_program_id_and_event(self, program_id) -> Sequence[Contract]:
        stmt = (
            select(Contract)
            .join(DerDispatch, DerDispatch.contract_id == Contract.id)
            .where(Contract.program_id == program_id)
        )
        return self.session.execute(stmt).unique().scalars().all()

    def get_contracts_by_service_provider_id(self, service_provider_id: int) -> Sequence[Contract]:
        stmt = select(Contract).where(Contract.service_provider_id == service_provider_id)
        return self.session.execute(stmt).unique().scalars().all()

    def get_contract_by_unique_constraint(
        self, program_id: int, service_provider_id: int, der_id: str
    ) -> Optional[Contract]:
        stmt = select(Contract).where(
            and_(
                Contract.program_id == program_id,
                Contract.service_provider_id == service_provider_id,
                Contract.der_id == der_id,
                Contract.contract_status != ContractStatus.SYSTEM_CANCELLED,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_unexpired_contracts_by_der_id(
        self, der_id: str, eager_load_relationship=True
    ) -> Sequence[Contract]:
        stmt = select(Contract).where(
            and_(
                Contract.der_id == der_id,
                Contract.contract_status != ContractStatus.EXPIRED,
                Contract.contract_status != ContractStatus.SYSTEM_CANCELLED,
            )
        )
        if eager_load_relationship:
            stmt = stmt.options(joinedload(Contract.der))
        contracts = self.session.execute(stmt).unique().scalars().all()
        return contracts

    def get_enrollment_and_program_by_contract_id(
        self,
        contract_id: int,
    ) -> Optional[EnrollmentRequest]:
        """Gets the enrollment request and program by contract id"""
        stmt = (
            select(EnrollmentRequest)
            .options(
                joinedload(EnrollmentRequest.program).options(
                    joinedload(Program.dispatch_max_opt_outs),
                    joinedload(Program.avail_operating_months),
                    joinedload(Program.avail_service_windows),
                )
            )
            .where(EnrollmentRequest.id == Contract.enrollment_request_id)
            .where(Contract.id == contract_id)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_contracts_to_activate(self) -> Sequence[Contract]:
        stmt = (
            select(Contract)
            .join(Program, Contract.program_id == Program.id, isouter=True)
            .where(
                and_(
                    Contract.contract_status == ContractStatus.ACCEPTED,
                    Program.status == ProgramStatus.ACTIVE,
                )
            )
        )
        return self.session.execute(stmt).scalars().all()

    def get_contracts_to_expire(self) -> Sequence[Contract]:
        stmt = (
            select(Contract)
            .join(Program, Contract.program_id == Program.id, isouter=True)
            .where(
                or_(
                    and_(
                        Contract.contract_status == ContractStatus.ACTIVE,
                        Program.status == ProgramStatus.ARCHIVED,
                    ),
                    and_(
                        Contract.contract_status == ContractStatus.ACCEPTED,
                        Program.status == ProgramStatus.ARCHIVED,
                    ),
                )
            )
        )
        return self.session.execute(stmt).scalars().all()


class ContractNotFound(Error):
    pass
