from datetime import datetime
from typing import Generator, Optional, Sequence

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from pm.modules.enrollment.enums import ContractStatus
from pm.modules.enrollment.models.enrollment import Contract
from pm.modules.event_tracking.builders.der_dispatch_dicts import InsertDerDispatchDict
from pm.modules.event_tracking.constraints import Constraint, ConstraintsBuilder
from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.event_tracking.models.der_response import (
    CreateDerResponseDict,
    DerResponse,
)
from pm.modules.progmgmt.models.program import Program
from pm.modules.reports.models.report import EventDetails
from shared.repository import SQLRepository


class EventRepository(SQLRepository):
    def _get_der_dispatch_constraints(
        self, contract_id: int, constraints: list[Constraint]
    ) -> list[Constraint]:
        """Gets the constraints that need to sum the der dispatches,
        ignoring any dispatches that have an opt out
        """
        sums = [
            func.sum(
                case(
                    (
                        DerDispatch.start_date_time >= c.timestamp,
                        c.event_property,
                    )
                )
            )
            for c in constraints
        ]
        stmt = (
            select(*sums)
            .outerjoin(DerResponse, DerResponse.control_id == DerDispatch.control_id)
            .where(
                DerDispatch.contract_id == contract_id,
                or_(DerResponse.is_opt_out.is_(False), DerResponse.is_opt_out.is_(None)),
            )
            .group_by(DerDispatch.contract_id)
        )
        result = self.session.execute(stmt).one_or_none()
        if result:
            for i, r in enumerate(result):
                constraints[i].set_value(r)
        return constraints

    def _get_opt_out_constraints(
        self, contract_id: int, constraints: list[Constraint]
    ) -> list[Constraint]:
        """Count the number of events with an opt out for each constraint timeperiod"""
        counts = [
            func.count(case((DerDispatch.start_date_time >= c.timestamp, 1), else_=None))
            for c in constraints
        ]
        stmt = (
            select(*counts)
            .join(
                DerResponse,
                and_(
                    DerResponse.control_id == DerDispatch.control_id,
                    DerResponse.is_opt_out.is_(True),
                ),
            )
            .where(
                DerDispatch.contract_id == contract_id,
            )
        )
        result = self.session.execute(stmt).one_or_none()
        if result:
            for i, r in enumerate(result):
                constraints[i].set_value(r)
        return constraints

    def _get_event_count_constraints(
        self, contract_id: int, constraints: list[Constraint]
    ) -> list[Constraint]:
        """Count the number of events that don't have an opt out for each constraint timeperiod"""
        counts = [
            func.count(case((DerDispatch.start_date_time >= c.timestamp, 1), else_=None))
            for c in constraints
        ]
        stmt = (
            select(*counts)
            .outerjoin(DerResponse, DerResponse.control_id == DerDispatch.control_id)
            .where(
                DerDispatch.contract_id == contract_id,
                or_(DerResponse.is_opt_out.is_(False), DerResponse.is_opt_out.is_(None)),
            )
        )
        result = self.session.execute(stmt).one_or_none()
        if result:
            for i, r in enumerate(result):
                constraints[i].set_value(r)
        return constraints

    def calculate_contract_constraints(
        self, current_day: datetime, contract_id: int, program: Program
    ) -> ContractConstraintSummary:
        """Creates a constraint summary of program constraints for a contract for the current day"""
        constraints = ConstraintsBuilder.build(current_day, program)
        if constraints.der_dispatch:
            self._get_der_dispatch_constraints(contract_id, constraints.der_dispatch)
        if constraints.opt_out:
            self._get_opt_out_constraints(contract_id, constraints.opt_out)
        if constraints.event_count:
            self._get_event_count_constraints(contract_id, constraints.event_count)
        return ContractConstraintSummary.create_from_constraints(
            contract_id, current_day, constraints.return_all_constraints()
        )

    def get_all_active_contracts(self) -> Generator[Contract, None, None]:
        """Gets all contracts with a status of ACTIVE. Returns them in batches of 1000, and yields
        each contract one by one. Used for calculating constraints for all active contracts."""
        CONTRACTS_BATCH_SIZE = 1000
        stmt = (
            select(Contract)
            .join(Program, Program.id == Contract.program_id)
            .where(Contract.contract_status == ContractStatus.ACTIVE)
            .options(joinedload(Contract.program).joinedload(Program.dispatch_max_opt_outs))
        )
        for batch in self.session.execute(stmt).unique().yield_per(CONTRACTS_BATCH_SIZE):
            for contract in batch:
                yield contract

    def get_constraints_summary_by_contract_id(
        self, contract_id: int
    ) -> Optional[ContractConstraintSummary]:
        """Gets a ContractConstraintSummary by contract_id"""
        stmt = (
            select(ContractConstraintSummary)
            .where(ContractConstraintSummary.contract_id == contract_id)
            .order_by(ContractConstraintSummary.day.desc())
        )
        return self.session.execute(stmt).scalar()

    def get_constraints_summary_by_id(
        self, contract_constraint_id: int
    ) -> Optional[ContractConstraintSummary]:
        stmt = (
            select(ContractConstraintSummary)
            .where(ContractConstraintSummary.id == contract_constraint_id)
            .order_by(ContractConstraintSummary.day.desc())
        )
        return self.session.execute(stmt).scalar()

    def get_constraints_summary_by_contract_id_list(
        self, contract_id_list: list[int]
    ) -> Sequence[ContractConstraintSummary]:
        """Gets a ContractConstraintSummary by contract_id"""
        stmt = select(ContractConstraintSummary).where(
            ContractConstraintSummary.contract_id.in_(contract_id_list)
        )
        return self.session.execute(stmt).unique().scalars().all()

    def get_events_by_contract_id_list(self, contract_id_list: list[int]) -> Sequence[DerDispatch]:
        stmt = (
            select(DerDispatch)
            .join(DerResponse, DerResponse.control_id == DerResponse.control_id)
            .filter(DerDispatch.contract_id.in_(contract_id_list))
            .filter(DerResponse.is_opt_out.is_(False))
        )
        return self.session.execute(stmt).unique().scalars().all()

    def get_event_details(self, report_id: int) -> Sequence[EventDetails]:
        """Gets event details by report_id"""
        stmt = select(EventDetails).where(EventDetails.report_id == report_id)
        return self.session.execute(stmt).unique().scalars().all()

    def filter_contract_id_set(self, contract_ids: set[int]) -> set[int]:
        """Filters a list of contract ids from a list of ids.
        Returns a set of ids that exist in the database.
        """
        stmt = select(Contract.id).where(Contract.id.in_(contract_ids))
        r = self.session.execute(stmt).unique().scalars().all()
        return set(r)

    def _filter_der_id_set(self, data: list[CreateDerResponseDict]) -> list[CreateDerResponseDict]:
        """Filters a list of der ids in contracts from a list of ids.
        Returns a list of ids that exist in the contract table.
        """
        der_ids = {d["der_id"] for d in data}
        stmt = select(Contract.der_id).where(Contract.der_id.in_(der_ids))
        r = self.session.execute(stmt).unique().scalars().all()
        response_set = set(r)
        return [d for d in data if d["der_id"] in response_set]

    def bulk_insert_der_dispatches(self, dispatches: list[InsertDerDispatchDict]):
        """Bulk insert dispatches from dictionaries"""
        self.session.execute(insert(DerDispatch), dispatches)

    def bulk_insert_der_responses(self, responses: list[CreateDerResponseDict]):
        """Bulk insert der responses from dictionaries. Will first check if the der_id
        exists in the contract table, and will insert the response record if it does.
        """
        filtered_responses = self._filter_der_id_set(responses)
        if filtered_responses:
            self.session.execute(insert(DerResponse), filtered_responses)
