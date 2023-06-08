import json
from http import HTTPStatus

import pytest

from pm.modules.enrollment.enums import ContractStatus
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin
from shared.enums import ProgramTypeEnum


class TestActiveInactiveServiceProvider(TestDataMixin):
    """As a utility I need the platform to support creation of service providers so that
    I can have them participate in DER/DR programs to ensure reliability of the grid I am
    responsible for.
    """

    def test_deactivate_service_provider(self, client, db_session):
        """BDD PM-1320

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user Sends POST Request
         And user creates an ACTIVE service provider in the system
        When user submit a PATCH request to /api/serviceprovider/1/disable
        Then the user receives HTTP Response code 200
         And user retreives the service provider by executing GET request to /api/serviceprovider/1
         And user finds the service provider status to be INACTIVE"""
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

        resp = client.patch("/api/serviceprovider/1/disable")
        assert resp.json == {"Disabled Service provider with id": 1}

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "INACTIVE"

    def test_activate_service_provider(self, client, db_session):
        """BDD PM-1321

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets the status field in the data to be INACTIVE
         And the user Sends POST Request
         And user creates an INACTIVE service provider in the system
        When user submit a PATCH request to /api/serviceprovider/1/enable
        Then the user receives HTTP Response code 200
         And user retreives the service provider by executing GET request to /api/serviceprovider/1
         And user finds the service provider status to be ACTIVE"""
        fileName = "valid_service_provider_data_all_fields.json"
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        body["general_fields"]["status"] = "INACTIVE"
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "INACTIVE"

        resp = client.patch("/api/serviceprovider/1/enable")
        assert resp.json == {"Enabled Service provider with id": 1}

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "ACTIVE"

    def test_failed_activate_service_provider_already_active(self, client, db_session):
        """BDD PM-1322:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets the status field in the data to be ACTIVE
         And the user Sends POST Request
         And user creates an ACTIVE service provider in the system
        When user submit a PATCH request to /api/serviceprovider/1/enable
        Then the user receives HTTP Response code 404
         And the error message states that the service provider is already enabled"""
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

        resp = client.patch("/api/serviceprovider/1/enable")
        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert resp.json["message"] == "Service provider with id 1 is already enabled"

    def test_failed_deactivate_service_provider_already_deactive(self, client, db_session):
        """BDD PM-1323:

        Given the user sets POST request endpoint /api/serviceProvider/
         And the user sets Request Header  Content-Type    application/json
         And the user sets Request Body from filename.json
         And the user sets the status field in the data to be INACTIVE
         And the user Sends POST Request
         And user creates an INACTIVE service provider in the system
        When user submit a PATCH request to /api/serviceprovider/1/disable
        Then the user receives HTTP Response code 404
         And the error message states that the service provider is already disabled"""
        fileName = "valid_service_provider_data_all_fields.json"
        filename = self._get_test_data_path(fileName)
        with open(filename, "r") as file:
            body = json.load(file)
        body["general_fields"]["status"] = "INACTIVE"
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.get("/api/serviceprovider/1")
        assert resp.json["status"] == "INACTIVE"

        resp = client.patch("/api/serviceprovider/1/disable")
        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert resp.json["message"] == "Service provider with id 1 is already disabled"

    @pytest.mark.parametrize(
        "body,program_type,response",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                    demand_response=dict(
                        import_target_capacity=300.01,
                        export_target_capacity=300.01,
                    ),
                ),
                ProgramTypeEnum.DEMAND_MANAGEMENT,
                "CREATED",
                id="all-fields",
            )
        ],
    )
    def test_contract_system_cancalled_when_service_provider_disabled(
        self, client, db_session, body, program_type, response
    ):
        """BDD Scenario PM-1324:
        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing single enrollment's fields data as
            json object nested in a list
        And the user Sends POST Request
        And the user receives HTTP Response code 200
        And the user check that there is a contract in the system with status
            not equal to SYSTEM_CANCELLED
        When user disable the servcie provider by sending a PATCH request to
            /api/serviceprovider/1/disable
        Then user retrieves the earlier contract in the system by GET request to /api/contract/1
        And the contract has been set to status SYSTEM_CANCELLED
        """
        factories.ProgramFactory(id=body["general_fields"]["program_id"], program_type=program_type)
        service_provider_id = body["general_fields"]["service_provider_id"]
        factories.ServiceProviderFactory(id=service_provider_id)
        der_id = body["general_fields"]["der_id"]
        factories.DerFactory(der_id=der_id)
        resp = client.post(
            f"/api/serviceprovider/{service_provider_id}/associate_ders",
            json=[{"der_id": der_id}],
        )
        assert resp.json[0]["status_code"] == 3
        resp = client.post("/api/enrollment/", json=[body])
        assert resp.json[0]["status"] == response

        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] != ContractStatus.SYSTEM_CANCELLED.value

        resp = client.patch("/api/serviceprovider/1/disable")
        assert resp.json == {"Disabled Service provider with id": 1}

        resp = client.get("/api/contract")
        assert resp.json[0]["contract_status"] == ContractStatus.SYSTEM_CANCELLED.value
