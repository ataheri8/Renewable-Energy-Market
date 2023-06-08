from __future__ import annotations

import functools
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from operator import add
from typing import Optional, Sequence, Tuple

from dataclasses_json import DataClassJsonMixin

from pm.modules.enrollment.models.enrollment import Contract
from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.reports.enums import ReportTypeEnum
from pm.modules.reports.models.report import EventDetails, Report
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ReportService:
    def generate_report(self, data: CreateReport) -> Report:
        """Create a program report.
        Requires program report data.
        """

        data_mapping = data.to_dict()
        report = Report(**data_mapping)  # type: ignore
        logger.info("Created Report")
        return report

    def update_report_fields(
        self,
        report: Report,
        contracts: Sequence[Contract],
        events: Sequence[DerDispatch],
        constraints: Sequence[ContractConstraintSummary],
    ):
        """Create a program report.
        Requires program report data.
        """

        self.update_event_details(report, contracts, events, constraints)
        self.update_contract_details(report, contracts, events)

    def update_contract_details(
        self, report: Report, contracts: Sequence[Contract], events: Sequence[DerDispatch]
    ):
        # setting total dispatched der's
        total_ders = set()
        uniquely_dispatched_ders = set()

        for contract in contracts:
            der_id = contract.der_id

            total_ders.add(der_id)

        report.total_der_in_program = len(total_ders)

        # setting up uniquely dispatched der's
        for event in events:
            uniquely_dispatched_ders.add(event.contract_id)

        report.dispatched_der = len(total_ders)

    def update_event_details(
        self,
        report: Report,
        contracts: Sequence[Contract],
        events: Sequence[DerDispatch],
        constraints: Sequence[ContractConstraintSummary],
    ):
        # setting total events to the length of events for the report
        report.total_events = len(events)

        cumulative_event_time = [event.cumulative_event_duration_mins for event in events]

        try:
            total_hours = functools.reduce(add, cumulative_event_time) / 60
            report.average_event_duration = Decimal(round(total_hours / len(events)))
        except (ZeroDivisionError, TypeError):
            report.average_event_duration = Decimal(0.0)
            logger.debug("no events found: unable to calculate event duration")

        dispatched_contracts = [event.contract_id for event in events]
        der_total = set()
        dispatched_der_total = set()

        for contract in contracts:
            # adding der to der total set for every contract
            der_total.add(contract.der_id)

            # checking if contract exists in dispatch_contracts list. If so
            # add it to the dispatched_der_total set
            if contract.id in dispatched_contracts:
                dispatched_der_total.add(contract.der_id)

            # adding up import and export target capacity and adding to report values
            if not report.avail_flexibility_up or not report.avail_flexibility_down:
                report.avail_flexibility_up = Decimal()
                report.avail_flexibility_down = Decimal()

            report.avail_flexibility_up += Decimal(
                contract.demand_response["import_target_capacity"]
            )
            report.avail_flexibility_down += Decimal(
                contract.demand_response["export_target_capacity"]
            )

        (
            report.constraint_violations,
            report.constraint_warnings,
        ) = self.calculate_contract_constraints(contracts, constraints)

        # setting der total
        report.total_der_in_program = len(der_total)
        # setting dispatched der total
        report.dispatched_der = len(dispatched_der_total)

    def create_event_details(
        self,
        report: Report,
        contracts: Sequence[Contract],
        dispatched_events: Sequence[DerDispatch],
        opted_out_events: Sequence[DerDispatch],
    ):
        (
            unique_ders,
            unique_opted_out_ders,
            requested_capacity,
            dispatched_capacity,
        ) = self._calculate_capacity(contracts, opted_out_events, dispatched_events)

        event_list = list()
        all_events = set(dispatched_events) | set(opted_out_events)
        for event in all_events:
            event_list.append(
                EventDetails(
                    report_id=report.id,
                    dispatch_id=event.event_id,
                    event_start=event.start_date_time,
                    event_end=event.end_date_time,
                    number_of_dispatched_der=len(unique_ders[event.contract_id]),
                    number_of_opted_out_der=len(unique_opted_out_ders[event.contract_id]),
                    requested_capacity=requested_capacity[event.contract_id],
                    dispatched_capacity=dispatched_capacity[event.contract_id],
                    event_status=event.event_status,
                )
            )

        return event_list

    def calculate_contract_constraints(
        self, contracts: Sequence[Contract], constraints: Sequence[ContractConstraintSummary]
    ) -> Tuple[int, int]:
        # Loop through each constraint, match the constraint object to the
        # Current contract_id and add all the violation and warning field
        # Values if any are true
        violations_count = 0
        warnings_count = 0
        contracts_by_id = {contract.id: contract for contract in contracts}
        for constraint_values in constraints:
            contract = contracts_by_id.get(constraint_values.contract_id)
            if contract:
                for field, value in vars(constraint_values).items():
                    (
                        constraint_violation,
                        constraint_warning,
                    ) = self._get_violations_and_warnings_count(field, value)
                    violations_count += constraint_violation
                    warnings_count += constraint_warning
        return violations_count, warnings_count

    def _get_violations_and_warnings_count(self, field, value) -> Tuple[int, int]:
        violations = 0
        warnings = 0

        violations = 1 if (re.match("_violation$", field) and value) else 0
        warnings = 1 if (re.match("_warning$", field) and value) else 0

        return violations, warnings

    def _calculate_capacity(self, contracts, opted_out_events, dispatched_events):
        opted_out_contract_ids = {event.contract_id for event in opted_out_events}
        dispatched_contract_ids = {event.contract_id for event in dispatched_events}

        unique_ders = defaultdict(set)
        unique_opted_out_ders = defaultdict(set)
        requested_capacity = defaultdict(Decimal)  # type: ignore
        dispatched_capacity = defaultdict(Decimal)  # type: ignore

        for contract in contracts:
            if contract.id in dispatched_contract_ids:
                unique_ders[contract.id].add(contract.der_id)
                self._add_target_capacity(dispatched_capacity, contract)
            if contract.id in opted_out_contract_ids:
                unique_opted_out_ders[contract.id].add(contract.der_id)
            self._add_target_capacity(requested_capacity, contract)

        return unique_ders, unique_opted_out_ders, requested_capacity, dispatched_capacity

    def _add_target_capacity(self, der_list, contract):
        der_list[contract.id] += (
            (contract.demand_response["import_target_capacity"]) if contract.demand_response else 0
        )


@dataclass
class CreateReport(DataClassJsonMixin):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    report_type: Optional[ReportTypeEnum] = None
    program_id: Optional[int] = None
    service_provider_id: Optional[int] = None
    start_report_date: Optional[datetime] = None
    end_report_date: Optional[datetime] = None
    created_by: Optional[str] = None
