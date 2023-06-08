from typing import Optional, Sequence

from sqlalchemy import asc, desc, select
from sqlalchemy.sql.selectable import Select

from pm.modules.enrollment.models.enrollment import Contract
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.event_tracking.models.der_response import DerResponse
from pm.modules.reports.enums import OrderType
from pm.modules.reports.models.report import ContractReportDetails, EventDetails, Report
from shared.exceptions import Error
from shared.repository import PaginatedQuery, SQLRepository


class ReportRepository(SQLRepository):
    def _build_contract_report_list_query(
        self, report_id: Optional[int], order_type: Optional[OrderType]
    ) -> Select:
        query = select(ContractReportDetails)

        if report_id is not None:
            query = query.where(ContractReportDetails.report_id == report_id)
        order = asc
        if order_type == OrderType.DESC:
            order = desc
        query = query.order_by(order(ContractReportDetails.enrollment_date))

        return query

    def _build_event_report_list_query(
        self, report_id: Optional[int], order_type: Optional[OrderType]
    ) -> Select:
        query = select(EventDetails)

        if report_id is not None:
            query = query.where(EventDetails.report_id == report_id)
        order = asc
        if order_type == OrderType.DESC:
            order = desc
        query = query.order_by(order(EventDetails.event_start))

        return query

    def get_all(self) -> Sequence[Report]:
        stmt = select(Report).order_by(Report.id)
        return self.session.execute(stmt).unique().scalars().all()

    def get(self, report_id) -> Optional[Report]:
        stmt = select(Report).where(Report.id == report_id)
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_report_or_raise(self, report_id: int) -> Report:
        """Gets the program by ID.
        Raise a ProgramNotFound exception if program does not exist"""
        report = self.get(report_id)
        if not report:
            raise ReportNotFound(f"Report with ID {report_id} not found")
        return report

    def get_contract_report_details(
        self,
        pagination_start,
        pagination_end,
        report_id: Optional[int] = None,
        order_type: Optional[OrderType] = None,
    ) -> PaginatedQuery[ContractReportDetails]:
        query = self._build_contract_report_list_query(report_id, order_type)
        return self.offset_paginate(query=query, start=pagination_start, end=pagination_end)

    def get_event_report_details(
        self,
        pagination_start,
        pagination_end,
        report_id: Optional[int] = None,
        order_type: Optional[OrderType] = None,
    ) -> PaginatedQuery[EventDetails]:
        query = self._build_event_report_list_query(report_id, order_type)
        return self.offset_paginate(query=query, start=pagination_start, end=pagination_end)

    def get_all_event_details(self):
        stmt = select(EventDetails)
        return self.session.execute(stmt).unique().scalars().all()

    def get_events_from_der_response(
        self, start, end, program_id, contract_id_list, dispatched
    ) -> Sequence[DerDispatch]:
        stmt = (
            select(DerDispatch)
            .outerjoin(DerResponse, DerResponse.control_id == DerDispatch.control_id)
            .join(Contract, Contract.id == DerDispatch.contract_id)
            .where(DerDispatch.start_date_time >= start)
            .where(DerDispatch.end_date_time <= end)
            .where(Contract.program_id == program_id)
            .where(Contract.id.in_(contract_id_list))
        )
        if dispatched:
            stmt = stmt.where(DerResponse.is_opt_out.is_(False))
        else:
            stmt = stmt.where(DerResponse.is_opt_out.is_(True))
        return self.session.execute(stmt).unique().scalars().all()


class ReportNotFound(Error):
    pass
