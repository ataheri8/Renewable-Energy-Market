from http import HTTPStatus

import pytest

from pm.tests_acceptance.mixins import TestDataMixin


class TestPM373(TestDataMixin):
    """An endpoint api/serviceprovider/upload to create one or multiple service providers via
    CSV file upload."""

    @pytest.mark.skip("Requires minio be running")
    def test_positive_scenario_upload_a_valid_csv_file(self, client, db_session) -> None:
        """BDD PM-374

        Given the user has a http client.
        When the user make a POST request to /api/serviceprovider/upload with a valid .csv file
        And with the following fields:
            | general_fields.name | MANDATORY |
            | general_fields.service_provider_type | MANDATORY |
            | primary_contact.email_address | MANDATORY |
            | primary_contact.phone_number | MANDATORY |
            | general_fields.status | MANDATORY |
            | address.street | OPTIONAL |
            | address.city | OPTIONAL |
            | address.state | OPTIONAL |
            | address.country | OPTIONAL |
            | address.zip_code | OPTIONAL |
        And with the following header "Content-Type: multipart/form-data"
        Then Service Providers are created
        And 201 status code is returned"""
        filename = self._get_test_data_path("valid_service_providers.csv")
        body = {"file": (open(filename, "rb"), filename)}
        resp = client.post(
            "/api/serviceprovider/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.CREATED

    def test_negative_scenario_upload_file_with_wrong_file_format(self, client) -> None:
        """BDD PM-379

        Given the user has a http client.
        When the user make a POST request to /api/serviceprovider/upload with a file with a
        random file format other than .csv
        And with the following header "Content-Type: multipart/form-data"
        Then Error message with the text "Invalid file type"
        And 422 status code is returned
        """
        filepath = self._get_test_data_path("invalid_file_type.json")
        body = {"file": (open(filepath, "rb"), filepath)}
        resp = client.post(
            "/api/serviceprovider/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.json["message"] == "Invalid file extension. Only CSV allowed"

    def test_negative_scenario_empty_file_is_uploaded(self, client) -> None:
        """BDD PM-428

        Given the user has a http client.
        When the user make a POST request to /api/serviceprovider/upload with empty file
        And with the following header "Content-Type: multipart/form-data"
        Then Error message with the text "Invalid/Missing file content"
        And 422 status code is returned
        """
        filepath = self._get_test_data_path("empty_file.csv")
        body = {"data": (open(filepath, "rb"), filepath)}
        resp = client.post(
            "/api/serviceprovider/upload",
            data=body,
            headers={"Content-Type": "multipart/form-data"},
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_negative_scenario_hitting_endpoint_without_a_file(self, client) -> None:
        """BDD PM-430

        Given the user has a http client.
        When the user make a POST request to /api/serviceprovider/upload without a file
        And with the following header "Content-Type: multipart/form-data"
        Then Error message with the text "Missing data for required field."
        And 422 status code is returned
        """
        resp = client.post(
            "/api/serviceprovider/upload", headers={"Content-Type": "multipart/form-data"}
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert resp.json["errors"]["files"]["file"][0] == "Missing data for required field."
