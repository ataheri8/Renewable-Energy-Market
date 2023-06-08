from typing import Dict, Sequence

from pm.modules.enrollment.contract_repository import ContractRepository
from pm.modules.enrollment.models.enrollment import Contract
from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.event_tracking.repository import EventRepository
from pm.modules.progmgmt.repository import ProgramRepository
from pm.modules.reports.enums import ReportTypeEnum
from pm.modules.reports.models.report import ContractReportDetails, EventDetails, Report
from pm.modules.reports.repository import ReportRepository
from pm.modules.reports.services.report import CreateReport, ReportService
from pm.modules.serviceprovider.repository import ServiceProviderRepository
from shared.exceptions import Error
from shared.repository import UOW, PaginatedQuery
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ReportUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.contract_repository = ContractRepository(self.session)
        self.event_repository = EventRepository(self.session)
        self.program_repository = ProgramRepository(self.session)
        self.service_provider_repository = ServiceProviderRepository(self.session)
        self.repository = ReportRepository(self.session)
        return self


class ReportController:
    def __init__(self):
        self.unit_of_work = ReportUOW()
        self.service = ReportService()

    def create_report(self, data: CreateReport):
        with self.unit_of_work as uow:
            if data.program_id:
                program = uow.program_repository.get(data.program_id)
                if not program:
                    logger.error("Cannot create without valid program")
                    raise InvalidReportArgs(message="Valid program required")
            elif data.service_provider_id:
                service_provider = uow.service_provider_repository.get_service_provider(
                    data.service_provider_id
                )
                if not service_provider:
                    logger.error("Cannot create without valid service_provider")
                    raise InvalidReportArgs(message="Valid service_provider required")
            report = self.service.generate_report(data)

            uow.repository.save(report)
            self._update_report_details(uow, report)
            self._update_contract_report_details(uow, report)
            self._update_event_details_report(uow, report)
            uow.commit()

    def _update_report_details(self, uow: ReportUOW, report: Report):
        contracts = self._get_contracts(uow, report)
        contract_id_list = [contract.id for contract in contracts]
        events = uow.event_repository.get_events_by_contract_id_list(contract_id_list)
        constraints = uow.event_repository.get_constraints_summary_by_contract_id_list(
            contract_id_list
        )

        self.service.update_report_fields(report, contracts, events, constraints)
        uow.repository.save(report)

    def _update_contract_report_details(self, uow: ReportUOW, report: Report):
        contracts = self._get_contracts(uow, report)
        contract_id_dict = {contract.id: contract for contract in contracts}
        constraints = uow.event_repository.get_constraints_summary_by_contract_id_list(
            list(contract_id_dict.keys())
        )

        self._create_contract_report_models(uow, report, constraints, contract_id_dict)

    def _create_contract_report_models(
        self,
        uow: ReportUOW,
        report: Report,
        constraints: Sequence[ContractConstraintSummary],
        contract_id_dict: Dict,
    ):
        for constraint in constraints:
            if constraint.contract_id in contract_id_dict:
                contract_report = ContractReportDetails(
                    enrollment_date=contract_id_dict[
                        constraint.contract_id
                    ].created_at,  # type: ignore
                    report_id=report.id,
                    der_id=contract_id_dict[constraint.contract_id].der_id,
                    service_provider_id=contract_id_dict[
                        constraint.contract_id
                    ].service_provider_id,
                    contract_constraint_id=constraint.id,
                )
                uow.repository.save(contract_report)
                continue

    def _update_event_details_report(self, uow: ReportUOW, report: Report):
        contracts = self._get_contracts(uow, report)
        contract_ids = {contract.id for contract in contracts}

        dispatched_events = uow.repository.get_events_from_der_response(
            report.start_report_date,
            report.end_report_date,
            report.program_id,
            contract_ids,
            dispatched=True,
        )
        opted_out_events = uow.repository.get_events_from_der_response(
            report.start_report_date,
            report.end_report_date,
            report.program_id,
            contract_ids,
            dispatched=False,
        )
        event_details_list = self.service.create_event_details(
            report, contracts, dispatched_events, opted_out_events
        )
        uow.repository.save_all(event_details_list)

    def _get_contracts(self, uow: ReportUOW, report: Report) -> Sequence[Contract]:
        if report.report_type == ReportTypeEnum.INDIVIDUAL_PROGRAM:
            return uow.contract_repository.get_contracts_by_program_id(report.program_id)
        else:
            return uow.contract_repository.get_contracts_by_service_provider_id(
                report.service_provider_id
            )

    def get_report(self, report_id: int) -> Report:
        with self.unit_of_work as uow:
            return uow.repository.get_report_or_raise(report_id)

    def get_all_reports(self) -> Sequence[Report]:
        with self.unit_of_work as uow:
            return uow.repository.get_all()

    def get_contract_report_details(self, query: dict) -> PaginatedQuery[ContractReportDetails]:
        with self.unit_of_work as uow:
            return uow.repository.get_contract_report_details(
                query["pagination_start"],
                query["pagination_end"],
                query["report_id"],
                query["order_type"],
            )

    def get_event_report_details(self, query: dict) -> PaginatedQuery[EventDetails]:
        with self.unit_of_work as uow:
            return uow.repository.get_event_report_details(
                query["pagination_start"],
                query["pagination_end"],
                query["report_id"],
                query["order_type"],
            )


class InvalidReportArgs(Error):
    pass


class InvalidReportDates(Error):
    pass
