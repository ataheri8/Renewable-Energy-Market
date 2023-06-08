from http import HTTPStatus

import pytest

from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin
from shared.minio_manager import MinioManager


class TestPM881(TestDataMixin):
    @pytest.mark.skip(reason="This test is end-to-end and requires some setup - see docstring")
    def test_upload_valid_der_assoc_csv(self, client, db_session):
        """
        Need minio_manager service to be running
        BDD Scenario: PM-882
        Given the user make a POST request to /api/serviceprovider/<service_provider_id>
        And upload a valid .csv file.
        And with the following fields: |der_rdf_id|
        And with the following header "Content-Type: multipart/form-data"
        Then DERs are associated with the Service Provider
        And 202 status code is returned
        """
        minio_manager = MinioManager()
        minio_manager.ensure_bucket_exists("target")
        filename = "valid_service_provider_der_association.csv"
        filepath = self._get_test_data_path(filename)
        factories.ServiceProviderFactory(id=1)
        body = {"file": (open(filepath, "rb"), filename)}
        old_files_in_bucket = len(minio_manager.list_files("target"))
        resp = client.post(
            "/api/serviceprovider/1/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        new_files_in_bucket = len(minio_manager.list_files("target"))
        assert resp.status_code == HTTPStatus.ACCEPTED
        assert new_files_in_bucket == old_files_in_bucket + 1
        # Fix this file delete later
        # minio_manager.delete_file(file_name=filename)

    def test_upload_invalid_der_assoc_file(self, client, db_session):
        """
        BDD Scenario: PM-884
        """
        factories.ServiceProviderFactory(id=1)
        filename = "invalid_file_type.json"
        filepath = self._get_test_data_path(filename)
        body = {"file": (open(filepath, "rb"), filename)}
        resp = client.post(
            "/api/serviceprovider/1/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.json["message"] == "Invalid file extension. Only CSV allowed"

    def test_upload_invalid_service_provider_id(self, client, db_session):
        """
        BDD Scenario: PM 885
        """
        factories.ServiceProviderFactory(id=1)
        filename = "valid_service_provider_der_association.csv"
        filepath = self._get_test_data_path(filename)
        invalid_service_provider_id = 99999999
        body = {"file": (open(filepath, "rb"), filename)}
        resp = client.post(
            f"/api/serviceprovider/{invalid_service_provider_id}/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert (
            resp.json["message"]
            == f"Service Provider with id {invalid_service_provider_id} is not found"
        )

    def test_upload_enrollment_no_file(self, client, db_session):
        factories.ServiceProviderFactory(id=1)
        body = {}
        resp = client.post(
            "/api/serviceprovider/1/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert resp.json["errors"]["files"]["file"][0] == "Missing data for required field."
