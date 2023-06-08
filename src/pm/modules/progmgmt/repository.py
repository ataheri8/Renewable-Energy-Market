from datetime import datetime
from typing import Optional, Sequence

import pendulum
from sqlalchemy import and_, asc, desc, select, text
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Select

from pm.modules.progmgmt.enums import OrderType, ProgramOrderBy, ProgramStatus
from pm.modules.progmgmt.models.program import HolidayCalendarsDict, Program
from shared.enums import ProgramTypeEnum
from shared.exceptions import Error
from shared.repository import PaginatedQuery, SQLRepository


class ProgramRepository(SQLRepository):
    def get_all(self) -> Sequence[Program]:
        stmt = select(Program).order_by(Program.id)
        return self.session.execute(stmt).unique().scalars().all()

    def _build_program_list_query(
        self,
        order_by: Optional[ProgramOrderBy] = None,
        order_type: Optional[OrderType] = None,
        status: Optional[ProgramStatus] = None,
        program_type: Optional[ProgramTypeEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Select:
        query = select(Program)
        if status is not None:
            query = query.where(Program.status == status)
        if program_type is not None:
            query = query.where(Program.program_type == program_type)
        if start_date is not None:
            query = query.where(Program.start_date is not None and Program.start_date >= start_date)
        if end_date is not None:
            query = query.where(Program.end_date is not None and Program.end_date <= end_date)

        order = asc
        if order_type == OrderType.DESC:
            order = desc

        if order_by == ProgramOrderBy.CREATED_AT:
            query = query.order_by(order(Program.created_at))
        elif order_by == ProgramOrderBy.PROGRAM_TYPE:
            query = query.order_by(order(Program.program_type))
        elif order_by == ProgramOrderBy.NAME:
            query = query.order_by(order(Program.name))
        elif order_by == ProgramOrderBy.START_DATE:
            query = query.order_by(order(Program.start_date))
        elif order_by == ProgramOrderBy.END_DATE:
            query = query.order_by(order(Program.end_date))

        if order_by is None:
            query = query.order_by(
                text(
                    "CASE status "
                    "WHEN 'DRAFT' THEN 1 "
                    "WHEN 'ACTIVE' THEN 2 "
                    "WHEN 'PUBLISHED' THEN 3 "
                    "WHEN 'ARCHIVED' THEN 4 "
                    "END, start_date "
                )
            )
        return query

    def get_paginated_list(
        self,
        pagination_start,
        pagination_end,
        order_by: Optional[ProgramOrderBy] = None,
        order_type: Optional[OrderType] = None,
        status: Optional[ProgramStatus] = None,
        program_type: Optional[ProgramTypeEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PaginatedQuery[Program]:
        query = self._build_program_list_query(
            order_by,
            order_type,
            status,
            program_type,
            start_date,
            end_date,
        )
        return self.offset_paginate(query=query, start=pagination_start, end=pagination_end)

    def count_by_name(self, name: str) -> int:
        stmt = select(Program.id).where(Program.name == name)
        return self.count(stmt)

    def get(
        self, program_id: int, include_draft=False, eager_load_relationships=True
    ) -> Optional[Program]:
        """Gets the program"""
        stmt = select(Program).where(Program.id == program_id)
        if not include_draft:
            stmt = stmt.where(Program.status != ProgramStatus.DRAFT)
        if eager_load_relationships:
            stmt = stmt.options(
                joinedload(Program.dispatch_max_opt_outs),
                joinedload(Program.dispatch_notifications),
                joinedload(Program.avail_operating_months),
                joinedload(Program.avail_service_windows),
            )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_program_or_raise(
        self, program_id: int, include_draft=False, eager_load_relationships=True
    ) -> Program:
        """Gets the program by ID.
        Raise a ProgramNotFound exception if program does not exist.

        Optionally allows you to include draft programs in the query.
        """
        program = self.get(
            program_id, include_draft=True, eager_load_relationships=eager_load_relationships
        )
        if not program:
            raise ProgramNotFound(f"program with ID {program_id} not found")
        elif program.status == ProgramStatus.DRAFT and not include_draft:
            raise ProgramNotFound(f"program with ID {program_id} is in draft status")
        return program

    def get_programs_to_activate(self) -> Sequence[Program]:
        stmt = select(Program).where(
            and_(Program.status == ProgramStatus.PUBLISHED, Program.start_date <= pendulum.now())
        )
        return self.session.execute(stmt).scalars().all()

    def get_programs_to_archive(self) -> Sequence[Program]:
        stmt = select(Program).where(
            and_(Program.status == ProgramStatus.ACTIVE, Program.end_date <= pendulum.now())
        )
        return self.session.execute(stmt).scalars().all()

    def delete_draft_program(self, program_id: int):
        """Hard delete a program if the status is DRAFT"""
        program = self.get_program_or_raise(program_id, include_draft=True)
        if program.status != ProgramStatus.DRAFT:
            raise ProgramNotDraft(
                f"code 143: Program {program.name} with ID {program.id}"
                + " is not a draft and cannot be deleted"
            )
        self.session.delete(program)

    def get_holiday_exclusions(self, program_id: int) -> Optional[HolidayCalendarsDict]:
        stmt = select(Program.holiday_exclusions).where(Program.id == program_id)
        return self.session.execute(stmt).scalar_one_or_none()


class ProgramNotDraft(Error):
    pass


class ProgramNotFound(Error):
    pass


class ProgramArchived(Error):
    pass
