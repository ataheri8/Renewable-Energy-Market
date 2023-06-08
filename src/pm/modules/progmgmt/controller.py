from pm.modules.enrollment.contract_repository import ContractRepository
from pm.modules.enrollment.enums import ContractStatus
from pm.modules.enrollment.services.contract import ContractService
from pm.modules.progmgmt.enums import ProgramStatus
from pm.modules.progmgmt.models.program import (
    CreateUpdateProgram,
    HolidayCalendarEventsDict,
    HolidayCalendarInfoDict,
    HolidayCalendarsDict,
    Program,
)
from pm.modules.progmgmt.repository import ProgramArchived, ProgramRepository
from shared.exceptions import Error
from shared.repository import UOW, PaginatedQuery
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ProgramUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.program_repository = ProgramRepository(self.session)
        self.contract_repository = ContractRepository(self.session)
        return self


class ProgramController:
    def __init__(self):
        self.unit_of_work = ProgramUOW()

    def create_program(self, data: CreateUpdateProgram):
        name = data.general_fields.name
        program_type = data.general_fields.program_type
        if not name or not program_type:
            logger.error("Cannot create Program without name or program_type")
            raise InvalidProgramArgs(message="Program name and type are required")
        with self.unit_of_work as uow:
            name_count = uow.program_repository.count_by_name(name)
            program = Program.factory(name, program_type, name_count)
            program.set_program_fields(data)
            uow.program_repository.save(program)
            uow.commit()

    def save_program(self, program_id: int, data: CreateUpdateProgram):
        with self.unit_of_work as uow:
            program = uow.program_repository.get_program_or_raise(program_id, include_draft=True)
            name = data.general_fields.name
            if name and name != program.name:
                name_count = uow.program_repository.count_by_name(name)
                program.set_name(name, name_count)
            program.set_program_fields(data)
            uow.program_repository.save(program)
            uow.commit()

    def save_holiday_exclusion(self, program_id: int, payload: HolidayCalendarsDict):
        with self.unit_of_work as uow:
            program = uow.program_repository.get_program_or_raise(program_id, include_draft=True)
            program.save_holiday_exclusion_program(payload)
            uow.program_repository.save(program)
            uow.commit()

    def archive_program(self, program_id: int):
        with self.unit_of_work as uow:
            program = uow.program_repository.get_program_or_raise(program_id, include_draft=True)
            program.set_program_status(ProgramStatus.ARCHIVED)
            uow.program_repository.save(program)
            self.expire_contract_for_archive_program(program_id)
            uow.commit()

    def expire_contract_for_archive_program(self, program_id: int):
        with self.unit_of_work as uow:
            contracts = uow.contract_repository.get_contracts_by_program_id(program_id)
            for contract in contracts:
                if ContractStatus.is_active_or_accepted(contract.contract_status):
                    contract = ContractService().update_contract_status(
                        contract, ContractStatus.EXPIRED
                    )
                    uow.contract_repository.save_update_contract(contract)
            uow.commit()

    def activate_programs(self):
        """Activate all programs that are published and with a start date in the past."""
        with self.unit_of_work as uow:
            programs = uow.program_repository.get_programs_to_activate()
            for program in programs:
                program.status = ProgramStatus.ACTIVE
                uow.program_repository.save(program)
            uow.commit()

    def archive_expired_programs(self):
        """Archive all programs that are active and with an end date in the past."""
        with self.unit_of_work as uow:
            programs = uow.program_repository.get_programs_to_archive()
            for program in programs:
                program.status = ProgramStatus.ARCHIVED
                uow.program_repository.save(program)
                self.expire_contract_for_archive_program(program.id)
            uow.commit()

    def delete_draft_program(self, program_id: int):
        """Delete a draft program. Will throw an error if the program is not a draft."""
        with self.unit_of_work as uow:
            uow.program_repository.delete_draft_program(program_id)
            uow.commit()

    def get_program(self, program_id: int) -> Program:
        with self.unit_of_work as uow:
            program = uow.program_repository.get_program_or_raise(program_id, include_draft=True)
            if program.status == ProgramStatus.ARCHIVED:
                raise ProgramArchived("Program with ID {program.id} is archived")
            return program

    def get_all_programs(self) -> list[Program]:
        with self.unit_of_work as uow:
            return uow.program_repository.get_all()

    def get_program_list(self, query: dict) -> PaginatedQuery[Program]:
        with self.unit_of_work as uow:
            return uow.program_repository.get_paginated_list(**query)

    def get_holiday_exclusions(self, program_id) -> list[HolidayCalendarEventsDict]:
        with self.unit_of_work as uow:
            calendars = uow.program_repository.get_holiday_exclusions(program_id)
            if not calendars:
                return []

            # Although multiple calendars are supported by the format we use, for now, our product
            # only supports one, so we select the first calendar...
            calendar: HolidayCalendarInfoDict = calendars["calendars"][0]
            return calendar["events"]


class ProgramNameDuplicate(Error):
    pass


class InvalidProgramArgs(Error):
    pass
