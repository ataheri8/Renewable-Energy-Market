import json
from http import HTTPStatus

from pm.tests_acceptance.mixins import TestDataMixin


class TestUniqueNameServiceProvider(TestDataMixin):
    """As a utility I need the platform to support creation of service providers so that
    I can have them participate in DER/DR programs to ensure reliability of the grid I am
    responsible for.
    """

    def test_failed_creation_service_provider_duplicate_name(self, client, db_session):
        """BDD PM-1335:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user Sends POST Request
         And user creates an ACTIVE service provider in the system
        When user submit a POST request to /api/serviceprovider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         with the same name as previoud Service Provider
        Then the user receives HTTP Response code 400
         And user receive error message saying that the name already exist"""
        fileName = "valid_service_provider_data_all_fields.json"
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "ACTIVE"

        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.json["message"] == "name already exists"

    def test_successful_create_service_provider_with_different_name(self, client, db_session):
        """BDD PM-1336:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user Sends POST Request
         And user creates an ACTIVE service provider in the system
        When user submit a POST request to /api/serviceprovider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json and chnages the name to a different one
        Then the user receives HTTP Response code 201
         And user retrevies the total number of service provider in the system
          by executing GET /api/serviceprovider
         And user finds there are 2 service providers in the system"""
        fileName = "valid_service_provider_data_all_fields.json"
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "ACTIVE"
        first_name = resp.json["name"]
        body["general_fields"]["name"] = "ABC_" + first_name
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/")
        assert len(resp.json) == 2
        assert resp.json[1]["name"] == "ABC_" + first_name

    def test_failed_update_service_provider_name_that_already_exist(self, client, db_session):
        """BDD PM-1338:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user Sends POST Request
         And user creates an ACTIVE service provider in the system
         And user submit a POST request to /api/serviceprovider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json and chnages the name to a different one
        When user submit a PATCH request to /api/serviceprovider/2
         And user has intention of setting the name of second service provider
           as same as name of first service provider
        Then the user receives HTTP Response code 400
         And the error message is that name already exist"""
        fileName = "valid_service_provider_data_all_fields.json"
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "ACTIVE"
        first_name = resp.json["name"]
        body["general_fields"]["name"] = "ABC_" + first_name
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/")
        assert len(resp.json) == 2
        assert resp.json[1]["name"] == "ABC_" + first_name

        body["general_fields"]["name"] = first_name
        resp = client.patch("/api/serviceprovider/2", json=body)
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.json["message"] == "name already exists"

    def test_successful_update_service_provider_name_that_already_exist_but_deleted(
        self, client, db_session
    ):
        """BDD PM-1337:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user Sends POST Request
         And user creates an ACTIVE service provider in the system
         And user submit a POST request to /api/serviceprovider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json and chnages the name to a different one
         with the same name as previoud Service Provider
         And user delete the first service provider by DELETE /api/serviceprovider/1
        When user submit a PATCH request to /api/serviceprovider/2
         And user has intention of setting the name of second service provider
           as same as name of first service provider
        Then the user receives HTTP Response code 200
         And the successfully verify that the name has chnaged"""
        fileName = "valid_service_provider_data_all_fields.json"
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "ACTIVE"
        first_name = resp.json["name"]
        body["general_fields"]["name"] = "ABC_" + first_name
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.delete("/api/serviceprovider/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        resp = client.get("/api/serviceprovider/")
        assert len(resp.json) == 1

        body["general_fields"]["name"] = first_name
        resp = client.patch("/api/serviceprovider/2", json=body)
        assert resp.status_code == HTTPStatus.OK

        resp = client.get("/api/serviceprovider/")
        assert len(resp.json) == 1
        assert resp.json[0]["name"] == first_name
