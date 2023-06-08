from http import HTTPStatus

import pytest

from pm.modules.progmgmt.enums import ProgramStatus
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin
from pm.tests_acceptance.program.base import TestProgramBase


class TestPM377(TestProgramBase, TestDataMixin):
    # TODO BDDs inconsistent with the test cases in ticket
    """Support Uploading Holiday Calendar JSON"""

    @pytest.mark.parametrize(
        "filename",
        [
            "valid_json.json",
            "valid_json_file_too_large.json",
            "invalid_json_content.json",
            "invalid_json_extention.jsonx",
        ],
    )
    def test_create_holiday_exclusions(self, filename, client, db_session):
        """Given a program exists in the database
        When user calls POST endpoint
        And user provides json file formatted as shown in the implementation details
        Then response received is 201
        And the holidays will be added to the program

        Given a program exists in the database
        When user calls POST endpoint
        And the file size is greater than 1 MB
        Then response received is 413
        And program will return an error stating size of the file is too big

        Given a program exists in the database
        When user calls POST endpoint
        And the file is not formatted in proper json format or unexpected field/values
        Then response received is 422
        And program will return an error stating the file is invalid

        Given a program exists in the database
        When user calls POST endpoint
        And the file extention is not ".json"
        Then response received is 422
        And program will return an error stating file extention is invalid
        """
        program = factories.ProgramFactory()
        program_id = program.id

        filepath = self._get_test_data_path(filename)
        json_file = {"file": (open(filepath, "rb"), filepath)}

        resp = client.post(f"/api/program/{program_id}/holiday-exclusions", data=json_file)

        p = self._get_program(db_session, program_id)

        if filename == "valid_json.json":
            assert resp.status_code == HTTPStatus.CREATED
            assert p.holiday_exclusions
        elif filename == "valid_json_file_too_large.json":
            assert resp.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
            assert not p.holiday_exclusions
        elif filename == "invalid_json_content.json":
            assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
            assert not p.holiday_exclusions
        elif filename == "invalid_json_extention.jsonx":
            assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
            assert not p.holiday_exclusions

    def test_create_holiday_exclusions_not_found(self, client, db_session):
        """Given a program doesn't in the database
        When user archives the program
        Then response received is 404"""
        filepath = self._get_test_data_path("valid_json.json")
        json_file = {"file": (open(filepath, "rb"), filepath)}
        resp = client.post("/api/program/12345/holiday-exclusions", data=json_file)
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_create_holiday_exclusions_on_archived_program(self, client, db_session):
        """Given a program is archived
        When user archives the program again
        Then response received is 400"""
        # Create Program with ARCHIVED status
        program = factories.ProgramFactory(status=ProgramStatus.ARCHIVED)

        filepath = self._get_test_data_path("valid_json.json")
        json_file = {"file": (open(filepath, "rb"), filepath)}
        resp = client.post(f"/api/program/{program.id}/holiday-exclusions", data=json_file)
        assert resp.status_code == HTTPStatus.BAD_REQUEST
