import json
from http import HTTPStatus

from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin
from pm.tests_acceptance.program.base import TestProgramBase


class TestPM370(TestProgramBase, TestDataMixin):
    # TODO BDDs inconsistent with the test cases in ticket
    """Support Listing Holiday Calendar JSON for a Program"""

    def test_get_holiday_exclusions(self, client, db_session):
        """Given a program exists in the database
        When user calls GET endpoint
        Then response received is 200
        And the program will return a list of holidays associated to the program"""
        program = factories.ProgramFactory()
        program_id = program.id

        filename = "valid_json.json"
        filepath = self._get_test_data_path(filename)
        json_file = {"file": (open(filepath, "rb"), filepath)}
        with open(filepath, "r") as fp:
            json_data = fp.read()
            fp.close()

        resp = client.post(f"/api/program/{program_id}/holiday-exclusions", data=json_file)

        p = self._get_program(db_session, program_id)

        assert resp.status_code == HTTPStatus.CREATED
        assert p.holiday_exclusions

        resp = client.get(f"/api/program/{program_id}/holiday-exclusions")

        assert resp.json == json.loads(json_data)["calendars"][0]["events"]
