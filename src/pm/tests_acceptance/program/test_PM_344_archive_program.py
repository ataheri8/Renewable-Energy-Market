from http import HTTPStatus

from pm.modules.progmgmt.enums import ProgramStatus
from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase


class TestPM344(TestProgramBase):
    """As a utility, I need to archive a program"""

    def test_archive_program(self, client, db_session):
        """Given a program exists in the database
        When user archives the program
        Then response received is 200
        And the program status will be changed to archived
        """
        program = factories.ProgramFactory()
        program_id = program.id
        resp = client.patch(f"/api/program/{program_id}/archive")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        program = self._get_program(db_session, program_id)
        assert program
        assert program.status == ProgramStatus.ARCHIVED

    def test_archive_program_no_program_exists(self, client, db_session):
        """Given a program doesn't in the database
        When user archives the program
        Then response received is 404
        """
        resp = client.patch(
            f"/api/program/12345/archive",  # noqa: F541
        )
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_archive_program_already_archived(self, client, db_session):
        """Given a program is archived
        When user archives the program again
        Then response received is 404
        """
        program = factories.ProgramFactory(status=ProgramStatus.ARCHIVED)
        program_id = program.id
        resp = client.patch(f"/api/program/{program_id}/archive")
        assert resp.status_code == HTTPStatus.BAD_REQUEST
