from http import HTTPStatus

from pm.modules.enrollment.enums import ContractStatus
from pm.restapi.enrollment.validators.requests import UpdateContractSchema
from pm.tests import factories


class TestPM688:
    """As a program admin, I need to edit contractual agreements so
    that I can reflect any contract changes.
    """

    def test_update_contract_with_demand_mgmt(self, client, db_session):
        """BDD PM-733 (with demand management contract)

        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        When the user sent a PATCH request to /api/contract/<contract-id>
        And the user sends the new/updated values for the contractual agreements
        And the new/updated values are acceptable and in correct format
        Then user receives the response of HTTP code 200
        And the user receives the id of the contract which was updated
        """
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["demand_response"] is None

        body: UpdateContractSchema = dict(
            contract_type=resp.json["contract_type"],
            enrollment_request_id=resp.json["enrollment_request_id"],
            contract_status=resp.json["contract_status"],
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
            demand_response=dict(import_target_capacity=0.0, export_target_capacity=0.0),
        )
        resp = client.patch("/api/contract/1", json=body)
        assert resp.status_code == HTTPStatus.OK

        resp = client.get("/api/contract/1")
        assert resp.json["demand_response"] is not None
        assert resp.json["demand_response"]["import_target_capacity"] >= 0

    def test_update_contract_with_doe(self, client, db_session):
        """BDD PM-733 (with DOE contract)

        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        When the user sent a PATCH request to /api/contract/<contract-id>
        And the user sends the new/updated values for the contractual agreements
        And the new/updated values are acceptable and in correct format
        Then user receives the response of HTTP code 200
        And the user receives the id of the contract which was updated
        """
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["dynamic_operating_envelopes"] is None

        body: UpdateContractSchema = dict(
            contract_type=resp.json["contract_type"],
            enrollment_request_id=resp.json["enrollment_request_id"],
            contract_status=resp.json["contract_status"],
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        resp = client.patch("/api/contract/1", json=body)
        assert resp.status_code == HTTPStatus.OK

        resp = client.get("/api/contract/1")
        assert resp.json["dynamic_operating_envelopes"] is not None
        assert (
            resp.json["dynamic_operating_envelopes"]["default_limits_active_power_import_kw"] >= 0
        )

    def test_update_contract_fail(self, client, db_session):
        """BDD PM-734

        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        When the user sent a PATCH request to /api/contract/<contract-id>
        And the user sends the new/updated values for the contractual agreements
        And the new/updated values are either not acceptable or not in correct format
        Then user receives the response of HTTP code 400 (BAD_REQUEST)
        And the user receives the error message why the contract was not updated"""
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["dynamic_operating_envelopes"] is None

        body: UpdateContractSchema = dict(
            contract_type=resp.json["contract_type"],
            enrollment_request_id=resp.json["enrollment_request_id"],
            contract_status=resp.json["contract_status"],
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        resp = client.patch("/api/contract/1", json=body)
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert (
            resp.json["message"].lower()
            == ("Default Limits - Active Power Import " "(kW) should be provided").lower()
        )

        resp = client.get("/api/contract/1")
        assert resp.json["dynamic_operating_envelopes"] is None

    def test_update_contract_fail_not_found(self, client, db_session):
        """BDD PM-735

        Given the user is program admin
        And there is no contract in the system with what the user wants to update
        the contractual agreement values
        When the user sent a PATCH request to /api/contract/<non-exisintg-contract-id>
        And the user sends the new/updated values for the contractual agreements
        And the new/updated values are acceptable and in correct format
        Then user receives the response of HTTP code 404 (NOT_FOUND)
        And the user receives the error message why the contract was not updated"""
        body: UpdateContractSchema = dict(
            contract_type="ENROLLMENT_CONTRACT",
            enrollment_request_id=1,
            contract_status="ACTIVE",
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
        )
        resp = client.patch("/api/contract/1", json=body)
        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert resp.json["message"].lower() == ("Contract with id 1 is not found").lower()

    def test_update_contract_fail_not_active_contract(self, client, db_session):
        """BDD PM-735

        Given the user is program admin
        And there is no contract in the system with what the user wants to
        update the contractual agreement values
        When the user sent a PATCH request to /api/contract/<non-exisintg-contract-id>
        And the user sends the new/updated values for the contractual agreements
        And the new/updated values are acceptable and in correct format
        Then user receives the response of HTTP code 404 (NOT_FOUND)
        And the user receives the error message why the contract was not updated"""
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK

        resp = client.delete("/api/contract/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        resp = client.get("/api/contract/1")
        assert resp.json["contract_status"] == ContractStatus.USER_CANCELLED.value

        body: UpdateContractSchema = dict(
            contract_type=resp.json["contract_type"],
            enrollment_request_id=resp.json["enrollment_request_id"],
            contract_status=resp.json["contract_status"],
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
            demand_response=dict(import_target_capacity=0.0, export_target_capacity=0.0),
        )
        resp = client.patch("/api/contract/1", json=body)
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert (
            resp.json["message"].lower()
            == ("Contract cannot be updated as it is either cancelled or expired").lower()
        )

    def test_delete_contract(self, client, db_session):
        """BDD PM-736 & PM-739

        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        When the user sent a DELETE request to /api/contract/<contract-id>
        Then user receives the response of HTTP code 204 (NO_CONTENT)
        And the user get the contract by sending GET request to /api/contract/<contract-id>
        And the user can confirm that the contract is set with stauts with USER CANCELLED


        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        When the user sent a DELETE request to /api/contract/<contract-id>
        Then user receives the response of HTTP code 204 (NO_CONTENT)
        And the user get the contract by sending GET request to /api/contract/<contract-id>
        And the user can confirm that the contract can be retreived
        """
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["contract_status"] != ContractStatus.USER_CANCELLED.value

        resp = client.delete("/api/contract/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        resp = client.get("/api/contract/1")
        assert resp.json["contract_status"] == ContractStatus.USER_CANCELLED.value

    def test_delete_contract_not_deletable(self, client, db_session):
        """ " BDD PM-737
        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        And the contract is already expired or cancelled
        When the user sent a DELETE request to /api/contract/<contract-id>
        Then user receives the response of HTTP code 400 (BAD_REQUEST)
        And the user get the contract by sending GET request to /api/contract/<contract-id>
        And the user receives the error message why the contract was not cancelled
        """
        contract_id = 1
        factories.ContractFactory(id=contract_id, contract_status=ContractStatus.EXPIRED)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["contract_status"] != ContractStatus.ACCEPTED.value
        assert resp.json["contract_status"] != ContractStatus.ACTIVE.value

        resp = client.delete("/api/contract/1")
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert (
            resp.json["message"].lower() == ("The contract can not be cancelled with id 1").lower()
        )

    def test_delete_contract_not_found(self, client, db_session):
        """BDD PM-738

        Given the user is program admin
        And there is no contract in the system which the user wants to cancell
        And the contract is already expired or cancelled
        When the user sent a DELETE request to /api/contract/<non-existing-contract-id>
        Then user receives the response of HTTP code 404 (NOT_FOUND)
        And the user receives the error message why the contract was not cancelled
        """
        resp = client.delete("/api/contract/1")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_undo_delete_contract(self, client, db_session):
        """BDD PM-740

        Given the user is program admin
        And there is an accepted enrollement in the system which has created a contract
        And the contract has been ealrier cancelled
        When the user sent a PATCH request to /api/contract/<contract-id>/reactivate
        Then user receives the response of HTTP code 200 (OK)
        And the user get the contract by sending GET request to /api/contract/<contract-id>
        And the user can confirm that the contract is set with stauts with ACTIVE or
        ACCEPTED (based on the program start dates)"""
        contract_id = 1
        factories.ContractFactory(id=contract_id, contract_status=ContractStatus.USER_CANCELLED)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["contract_status"] != ContractStatus.ACTIVE.value
        assert resp.json["contract_status"] == ContractStatus.USER_CANCELLED.value

        resp = client.patch("/api/contract/1/reactivate")
        assert resp.status_code == HTTPStatus.OK

        resp = client.get("/api/contract/1")
        assert resp.json["contract_status"] == ContractStatus.ACCEPTED.value

    def test_undo_delete_contract_not_found(self, client, db_session):
        resp = client.patch("/api/contract/1/reactivate")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_undo_delete_contract_not_possible(self, client, db_session):
        contract_id = 1
        factories.ContractFactory(id=contract_id, contract_status=ContractStatus.EXPIRED)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["contract_status"] != ContractStatus.ACTIVE.value
        assert resp.json["contract_status"] == ContractStatus.EXPIRED.value

        resp = client.patch("/api/contract/1/reactivate")
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert (
            resp.json["message"].lower()
            == (
                "The contract cannot be re-activated as "
                + "previously it has not been cancelled by user"
            ).lower()
        )

        resp = client.get("/api/contract/1")
        assert resp.json["contract_status"] != ContractStatus.ACTIVE.value
