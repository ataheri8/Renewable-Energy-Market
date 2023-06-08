import json
from http import HTTPStatus

import pytest

from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


class TestPM405(TestDataMixin):
    """As a utility I need the platform to support creation of service providers so that
    I can have them participate in DER/DR programs to ensure reliability of the grid I am
    responsible for.
    """

    @pytest.mark.parametrize(
        "fileName",
        [
            pytest.param(
                "valid_service_provider_data_all_fields.json",
                id="all-fields",
            ),
            pytest.param(
                "valid_service_provider_data_min_fields.json",
                id="minimum-fields",
            ),
        ],
    )
    def test_create_service_provider_positive_scenario(self, client, db_session, fileName):
        """BDD PM-223

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
         And Response Body should not be empty"""
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

    def test_create_service_provider_negative_scenario(self, client, db_session):
        """BDD PM-224

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body with nothing
        When the user Sends POST request
        Then the user Receives HTTP response code 422
        """
        resp = client.post("/api/serviceprovider/", headers={"Content-Type": "application/json"})
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "fileName",
        [
            pytest.param(
                "valid_service_provider_data_all_fields.json",
                id="all-fields",
            ),
            pytest.param(
                "valid_service_provider_data_min_fields.json",
                id="minimum-fields",
            ),
        ],
    )
    def test_retrieve_a_service_provider_positive_scenario(self, client, db_session, fileName):
        """BDD PM-418

        Given the user sets GET request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets GET request endpoint /api/serviceProvider/1
        When the user sends GET request
        Then the user Recieves HTTP response code 201
         And the user Recieves valid ServiceProvider json
        """
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        resp = client.get("/api/serviceprovider/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json is not None

    def test_retrieve_a_service_provider_negative_scenario(self, client, db_session):
        """BDD PM-419

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets GET request endpoint /api/serviceProvider/1
        When the user sends GET request
        Then the user Recieves HTTP response code 404
        """
        resp = client.get("/api/serviceprovider/1")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_update_a_service_provider_positive_scenario(self, client, db_session):
        """BDD PM-420

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets PATCH request endpoint /api/serviceProvider/id
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename_patch.json
        When the user Sends PATCH Request
        Then the user receives HTTP Response code 201
         And Response Body should not be empty"""
        filename = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )

        filename = self._get_test_data_path("valid_service_provider_data_all_fields_patch.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.patch("/api/serviceprovider/1", json=body)
        assert resp.status_code == HTTPStatus.OK
        assert resp.response is not None

    def test_cannot_update_a_service_provider_status_by_patch(self, client, db_session):
        """BDD PM-1325:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets PATCH request endpoint /api/serviceProvider/id
         And the user sets Request Header  Content-Type    application/json
         And the user tries to change the status in the Patch request
        When the user Sends PATCH Request
        Then the user receives HTTP Response code 201
         And user retrieves the service provider
         And user finds that the status did not change in the service provider"""
        filename = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        resp = client.get("/api/serviceprovider/1")
        first_status = resp.json["status"]
        body["general_fields"]["status"] = "INACTIVE"
        resp = client.patch("/api/serviceprovider/1", json=body)
        assert resp.status_code == HTTPStatus.OK
        resp = client.get("/api/serviceprovider/1")
        second_status = resp.json["status"]
        assert first_status == second_status

    def test_update_a_service_provider_negative_scenario(self, client, db_session):
        """BDD PM-421

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets PATCH request endpoint /api/serviceProvider/ABC
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename_patch.json
        When the user Sends PATCH Request
        Then the user receives HTTP Response code 404
        """
        filename = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )

        filename = self._get_test_data_path("valid_service_provider_data_all_fields_patch.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.patch("/api/serviceprovider/ABC", json=body)
        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(
        "fileName",
        [
            pytest.param(
                "valid_service_provider_data_all_fields.json",
                id="all-fields",
            ),
            pytest.param(
                "valid_service_provider_data_min_fields.json",
                id="minimum-fields",
            ),
        ],
    )
    def test_delete_a_service_provider_positive_scenario(self, client, db_session, fileName):
        """BDD PM-422

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets DELETE request endpoint /api/serviceProvider/1
        When the user Sends DELETE Request
        Then the user receives HTTP Response code 204"""
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        resp = client.delete("/api/serviceprovider/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

    def test_delete_a_service_provider_negative_scenario(self, client, db_session):
        """BDD PM-423
        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets DELETE request endpoint /api/serviceProvider/id
        When the user Sends DELETE Request
        Then the user receives HTTP Response code 404
        """
        filename = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )

        resp = client.delete("/api/serviceprovider/ABC")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_create_service_provider_negative_scenario_wrong_header(self, client, db_session):
        """BDD PM-434
        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Body from filename.json
         And the user sets Request Header  Content-Type    text/plain
        When the user Sends POST request
        Then the user Receives HTTP response code 422
        """
        filename = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "text/plain"}, json=body
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_create_service_provider_with_invalid_input_values(self, client, db_session):
        """BDD PM-460
        Given the user sets POST request endpoint /api/serviceProvider/
        And the user sets Request Header  Content-Type    application/json
        And the user sets Request Body from filename_invalid_input.json
        When the user Sends POST Request
        Then the user receives HTTP Response code 422
        And Response Body has json object with Non Null errors field
        """
        filename = self._get_test_data_path(
            "valid_service_provider_data_all_fields_invalid_email.json"
        )
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert resp.json["errors"] is not None

    # non BDD tests
    def test_program_count_no_service_provider(self, client, db_session):
        resp = client.get("/api/serviceprovider/")
        assert resp.status_code == 200
        assert len(resp.json) == 0

    def test_get_service_provider(self, client, db_session):
        factories.ServiceProviderFactory()
        resp = client.get("/api/serviceprovider/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 1
        assert resp.json[0]["uuid"] is not None

    def test_single_crud_service_provider(self, client, db_session):
        filename = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filename, "r") as file:
            body = json.load(file)

        # get Operation for non-existing Service Provider
        resp = client.get("/api/serviceprovider/1", json=body)
        assert resp.status_code == HTTPStatus.NOT_FOUND

        # Create Operation
        resp = client.post("/api/serviceprovider/", json=body)
        assert resp.status_code == HTTPStatus.CREATED

        # Read Operation
        resp = client.get("/api/serviceprovider/1")
        assert resp.status_code == HTTPStatus.OK

        # Update Operation
        body["general_fields"]["name"] = body["general_fields"]["name"] + " updated"
        resp = client.patch("/api/serviceprovider/1", json=body)
        assert resp.status_code == HTTPStatus.OK

        # Delete Operation
        resp = client.delete("/api/serviceprovider/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        # Delete no service provider
        resp = client.delete("/api/serviceprovider/12345")
        assert resp.status_code == HTTPStatus.NOT_FOUND

        # get Operation for non-existing Service Provider
        resp = client.get("/api/serviceprovider/1", json=body)
        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(
        "value",
        ["", " ", "123NUM", "NUM123", "00000000", "ABC", "a", "1234567890"],
    )
    def test_phone_number_validation_negative(self, client, db_session, value):
        data = {
            "general_fields": {
                "name": "name",
                "service_provider_type": "AGGREGATOR",
                "status": "ACTIVE",
            },
            "primary_contact": {"email_address": "mlh@ge.com", "phone_number": value},
        }
        resp = client.post("/api/serviceprovider/", json=data)
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        error_msg = resp.json["errors"]["json"]["primary_contact"]["phone_number"][0]

        assert error_msg == "Phone number is not valid"

    def test_phone_number_validation_positive(self, client, db_session):
        data = {
            "general_fields": {
                "name": "name",
                "service_provider_type": "AGGREGATOR",
                "status": "ACTIVE",
            },
            "primary_contact": {"email_address": "mlh@ge.com", "phone_number": "4167445389"},
        }
        resp = client.post("/api/serviceprovider/", json=data)
        assert resp.status_code == HTTPStatus.CREATED

    def test_positive_empty_notification_contact(self, client) -> None:
        """
        BDD Scenario PM-1330:
        Given the user wants to create a service provider and hit the endpoint /api/serviceprovider
         with a POST request
         When the user sends the request with json body having empty string values for fields in
         the notification contact json object
        And the other required fields are present in the request body
        Then the user is still able to create a service provider
        """
        data = {
            "general_fields": {
                "name": "name",
                "service_provider_type": "AGGREGATOR",
                "status": "ACTIVE",
            },
            "primary_contact": {"email_address": "mlh@ge.com", "phone_number": "4167445389"},
            "notification_contact": {"email_address": "", "phone_number": ""},
        }
        resp = client.post("/api/serviceprovider/", json=data)
        assert resp.status_code == HTTPStatus.CREATED

    def test_failure_wrong_email_notification_contact(self, client) -> None:
        """
        BDD Scenario PM-1331:
        Given the user wants to create a service provider and hit the endpoint /api/serviceprovider
         with a POST request
         When the user sends the request with json body having incorrect string values for field
         email_address in the notification contact json object
        And the other required fields are present in the request body
        Then the user is not able to create a service provider
        """
        wrong_emails = ["abc", "abc@", "abc@abc"]
        for email in wrong_emails:
            data = {
                "general_fields": {
                    "name": "name__" + email,
                    "service_provider_type": "AGGREGATOR",
                    "status": "ACTIVE",
                },
                "primary_contact": {"email_address": "mlh@ge.com", "phone_number": "4167445389"},
                "notification_contact": {"email_address": email, "phone_number": ""},
            }
            resp = client.post("/api/serviceprovider/", json=data)
            assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_success_correct_email_notification_contact(self, client) -> None:
        """
        BDD Scenario PM-1332:
        Given the user wants to create a service provider and hit the endpoint /api/serviceprovider
         with a POST request
         When the user sends the request with json body having correct string values for field
         email_address in the notification contact json object
        And the other required fields are present in the request body
        Then the user is able to create a service provider
        """
        correct_emails = ["abc@abc.com", "abc@00.com"]
        for email in correct_emails:
            data = {
                "general_fields": {
                    "name": "name__" + email,
                    "service_provider_type": "AGGREGATOR",
                    "status": "ACTIVE",
                },
                "primary_contact": {"email_address": "mlh@ge.com", "phone_number": "4167445389"},
                "notification_contact": {"email_address": email, "phone_number": ""},
            }
            resp = client.post("/api/serviceprovider/", json=data)
            assert resp.status_code == HTTPStatus.CREATED

    def test_failure_wrong_phone_notification_contact(self, client) -> None:
        """
        BDD Scenario PM-1333:
        Given the user wants to create a service provider and hit the endpoint /api/serviceprovider
         with a POST request
         When the user sends the request with json body having incorrect string values for field
         phone_number in the notification contact json object
        And the other required fields are present in the request body
        Then the user is not able to create a service provider
        """
        wrong_phones = ["0", "1234567890", "012abc", "abc001"]
        for phone in wrong_phones:
            data = {
                "general_fields": {
                    "name": "name__" + phone,
                    "service_provider_type": "AGGREGATOR",
                    "status": "ACTIVE",
                },
                "primary_contact": {"email_address": "mlh@ge.com", "phone_number": "4167445389"},
                "notification_contact": {"email_address": "mlh@ge.com", "phone_number": phone},
            }
            resp = client.post("/api/serviceprovider/", json=data)
            assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_success_correct_phone_notification_contact(self, client) -> None:
        """
        BDD Scenario PM-1334:
        Given the user wants to create a service provider and hit the endpoint /api/serviceprovider
         with a POST request
         When the user sends the request with json body having correct string values for field
         phone_number in the notification contact json object
        And the other required fields are present in the request body
        Then the user is able to create a service provider
        """
        correct_phones = ["4165743612", "4167445389"]
        for phone in correct_phones:
            data = {
                "general_fields": {
                    "name": "name__" + phone,
                    "service_provider_type": "AGGREGATOR",
                    "status": "ACTIVE",
                },
                "primary_contact": {"email_address": "mlh@ge.com", "phone_number": "4167445389"},
                "notification_contact": {"email_address": "mlh@ge.com", "phone_number": phone},
            }
            resp = client.post("/api/serviceprovider/", json=data)
            assert resp.status_code == HTTPStatus.CREATED
