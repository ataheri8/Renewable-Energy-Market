from http import HTTPStatus

import pytest

from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin
from shared.minio_manager import MinioManager


class TestPM699(TestDataMixin):
    @pytest.mark.skip(reason="This test is end-to-end and requires some setup - see docstring")
    def test_upload_valid_enrollment_csv(self, client, db_session):
        """
        BDD Scenario: PM-700
        Need minio_manager service to be running
        """
        minio_manager = MinioManager()
        minio_manager.ensure_bucket_exists("target")
        filename = "valid_enrollment_requests.csv"
        filepath = self._get_test_data_path(filename)
        factories.ProgramFactory(id=1)
        factories.ServiceProviderFactory(id=1)
        body = {"file": (open(filepath, "rb"), filename)}
        old_files_in_bucket = len(minio_manager.list_files("target"))
        resp = client.post(
            "/api/enrollment/1/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        new_files_in_bucket = len(minio_manager.list_files("target"))
        assert resp.status_code == HTTPStatus.ACCEPTED
        assert new_files_in_bucket == old_files_in_bucket + 1
        # Fix this file delete later
        # minio_manager.delete_file(file_name=filename)

    def test_upload_invalid_enrollment_file_type(self, client, db_session):
        """
        BDD Scenario: PM 701
        """
        factories.ProgramFactory(id=1)
        filename = "invalid_file_type.json"
        filepath = self._get_test_data_path(filename)
        body = {
            "session_id": "session_id_123",
            "file": (open(filepath, "rb"), filename),
        }
        resp = client.post(
            "/api/enrollment/1/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.json["message"] == "Invalid file extension. Only CSV allowed"

    def test_upload_invalid_program_id(self, client, db_session):
        """
        BDD Scenario: PM 703
        """
        filename = "valid_enrollment_requests.csv"
        filepath = self._get_test_data_path(filename)
        invalid_program_id = 999999
        body = {"file": (open(filepath, "rb"), filename)}
        resp = client.post(
            f"/api/enrollment/{invalid_program_id}/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert resp.json["message"] == f"program with ID {invalid_program_id} not found"

    def test_upload_enrollment_no_file(self, client, db_session):
        factories.ProgramFactory(id=1)
        factories.ServiceProviderFactory(id=1)
        body = {}
        resp = client.post(
            "/api/enrollment/1/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert resp.json["errors"]["files"]["file"][0] == "Missing data for required field."
