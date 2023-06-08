from http import HTTPStatus

from pm.modules.progmgmt.enums import ProgramStatus
from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase


class TestPM1036(TestProgramBase):
    """As a user, I want to be able to delete a program when it's still in draft status"""

    def test_program_deleted_error(self, client, db_session):
        """BDD PM-1038

        Given a program exists
          And it is <not in DRAFT> status
        When the delete program draft endpoint is called
        Then the operation should fail
          And the endpoint should return a 403 status code
        """
        program_id = 1
        program = factories.ProgramFactory(id=program_id, status=ProgramStatus.PUBLISHED)
        resp = client.delete(f"/api/program/{program_id}")
        assert resp.status_code == HTTPStatus.FORBIDDEN
        program = self._get_program(db_session, program_id)
        assert program

    def test_deleted_program(self, client, db_session):
        """BDD PM-1037

        Given a program exists
          And it is in DRAFT status
        When the delete program draft endpoint is called
        Then the program is deleted
        """
        program_id = 1
        program = factories.ProgramFactory(id=program_id, status=ProgramStatus.DRAFT)
        resp = client.delete(f"/api/program/{program_id}")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        program = self._get_program(db_session, program_id)
        assert program is None
