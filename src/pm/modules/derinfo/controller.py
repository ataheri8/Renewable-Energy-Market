from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.derinfo.repository import DerInfoRepository, DerUpdate
from pm.modules.enrollment.contract_repository import ContractRepository
from shared.repository import UOW


class DerInfoUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.repository = DerInfoRepository(self.session)
        self.contract_repository = ContractRepository(self.session)
        return self


class DerInfoController:
    def __init__(self):
        self.unit_of_work = DerInfoUOW()

    def get_available_ders_not_in_program(self, program_id: int) -> list[DerInfo]:
        return self.get_ders_with_service_provider_but_no_contract(program_id)

    def upsert_der_from_kafka(self, data: DerUpdate) -> None:
        with self.unit_of_work as uow:
            uow.repository.upsert_der_from_kafka(data)
            uow.commit()

    def get_ders_with_service_provider_but_no_contract(self, program_id=None) -> list[DerInfo]:
        with self.unit_of_work as uow:
            ders = uow.repository.get_ders_with_sp_no_contract()
            ders_ret: list[DerInfo] = []
            for der in ders:
                contracts = uow.contract_repository.get_unexpired_contracts_by_der_id(
                    der_id=der.der_id
                )
                if program_id not in [c.program_id for c in contracts]:
                    ders_ret.append(der)

        return ders_ret

    def get_ders_with_no_service_provider(self) -> list[DerInfo]:
        with self.unit_of_work as uow:
            return uow.repository.get_ders_with_no_sp()

    def get_ders_in_program_with_enrollment(self, program_id: int) -> list[DerInfo]:
        with self.unit_of_work as uow:
            return uow.repository.get_ders_in_program_with_enrollment(program_id)
