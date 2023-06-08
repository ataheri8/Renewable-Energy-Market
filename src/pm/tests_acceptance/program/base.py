from sqlalchemy import select
from sqlalchemy.orm import joinedload

from pm.modules.progmgmt.models.program import Program


class TestProgramBase:
    """Base class for program tests"""

    def _get_programs(self, db_session):
        with db_session() as session:
            stmt = select(Program)
            return session.execute(stmt).scalars().all()

    def _get_program(self, db_session, program_id):
        with db_session() as session:
            stmt = (
                select(Program)
                .where(Program.id == program_id)
                .options(
                    joinedload(Program.dispatch_max_opt_outs),
                    joinedload(Program.dispatch_notifications),
                    joinedload(Program.avail_operating_months),
                    joinedload(Program.avail_service_windows),
                )
            )
            return session.execute(stmt).unique().scalar_one_or_none()
