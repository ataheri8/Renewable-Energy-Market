from http import HTTPStatus

from pm.tests import factories


class TestProgramSPEnrollmentContractDERAssoc:
    """This will test the different cases related to flow of the contracts by changing Program, SP,
    DER Association, Enrollment, Update of an existing contract
    """

    def _gen_raw_data(self, der_id: str):
        program_body = {
            "general_fields": {
                "name": "program_name",
                "program_type": "GENERIC",
                "start_date": "2022-05-10T04:00:00+00:00",
                "end_date": "2025-05-10T04:00:00+00:00",
                "status": "PUBLISHED",
            }
        }
        service_provider_body = {
            "general_fields": {
                "name": "service_provider_name",
                "service_provider_type": "AGGREGATOR",
                "status": "ACTIVE",
            },
            "primary_contact": {"email_address": "mlh3@ge.com", "phone_number": "905-444-5566"},
            "notification_contact": {
                "email_address": "JohnDoe@ge.com",
                "phone_number": "905-334-7766",
            },
            "address": {
                "street": "123 Street",
                "city": "NoCity",
                "state": "NoState",
                "country": "NoCountry",
                "zip_code": "A1B2C3",
                "apt_unit": "105",
            },
        }

        enrollment_body = [
            {
                "general_fields": {"program_id": 1, "service_provider_id": 1, "der_id": der_id},
                "dynamic_operating_envelopes": {
                    "default_limits_active_power_import_kw": 5.1,
                    "default_limits_active_power_export_kw": 5.2,
                    "default_limits_reactive_power_import_kw": 5.3,
                    "default_limits_reactive_power_export_kw": 5.4,
                },
                "demand_response": {"import_target_capacity": 0.2, "export_target_capacity": 0.3},
            }
        ]
        sp_der_assoc_body = [{"der_id": der_id}]
        return {
            "program_body": program_body,
            "serviceprovider_body": service_provider_body,
            "serviceprovider_der_assoc_body": sp_der_assoc_body,
            "enrollment_body": enrollment_body,
        }

    def _create_prog_SP_DerAssoc_enrollment(self, client, der_id: str, req_body: dict):
        factories.DerFactory(id=1, der_id=der_id)

        program_resp = client.post("/api/program", json=req_body["program_body"])
        serviceprovider_resp = client.post(
            "/api/serviceprovider", json=req_body["serviceprovider_body"]
        )
        sp_id = serviceprovider_resp.json["Created Service provider with id"]
        serviceprovider_derAssoc_resp = client.post(
            f"/api/serviceprovider/{sp_id}/associate_ders",
            json=req_body["serviceprovider_der_assoc_body"],
        )
        req_body["enrollment_body"][0]["general_fields"]["service_provider_id"] = sp_id
        enrollment_resp = client.post("/api/enrollment", json=req_body["enrollment_body"])

        return {
            "program_resp": program_resp,
            "serviceprovider_resp": serviceprovider_resp,
            "serviceprovider_derAssoc_resp": serviceprovider_derAssoc_resp,
            "enrollment_resp": enrollment_resp,
        }

    def test_can_enroll_der_again_if_previously_system_cancelled(self, client, db_session):
        """BDD PM-1316

        Given the user is program admin
        And there is a service provider in the system
        And there is a der in the system which is assciated with the service provider
        And there is an accepted enrollement in the system which has created a contract
        When user has un-associated the der from the service provider
        And the contracts become System_cancelled
        And the user re-associate the der in the service provider
        And submit an enrollment request for the same der in the same program
        Then user receives that the enrollment request has been accepted
        And contract has been created
        """
        der_id = "test_der"
        req_body = self._gen_raw_data(der_id)
        resp_body = self._create_prog_SP_DerAssoc_enrollment(  # noqa: F841
            client=client, der_id=der_id, req_body=req_body
        )

        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "ACCEPTED"

        resp = client.delete("/api/serviceprovider/1/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        resp = client.get("/api/contract")
        assert resp.json[0]["contract_status"] == "SYSTEM_CANCELLED"

        resp = client.post(
            "/api/serviceprovider/1/associate_ders",
            json=req_body["serviceprovider_der_assoc_body"],
        )
        assert resp.json[0]["status_code"] == 3

        resp = client.post("/api/enrollment", json=req_body["enrollment_body"])
        resp = client.get("/api/contract")
        assert len(resp.json) == 2
        assert resp.json[1]["contract_status"] == "ACCEPTED"

    def test_cannot_enroll_der_again_if_previously_user_cancelled(self, client, db_session):
        """BDD PM-1317

        Given the user is program admin
        And there is a service provider in the system
        And there is a der in the system which is assciated with the service provider
        And there is an accepted enrollement in the system which has created a contract
        When user has delete the contract
        And the contracts become user_cancelled
        And the user submit an enrollment request for the same der in the same program
        Then user receives that the enrollment request has not been been accepted
        And contract has not been created
        """
        der_id = "test_der"
        req_body = self._gen_raw_data(der_id)
        resp_body = self._create_prog_SP_DerAssoc_enrollment(  # noqa: F841
            client=client, der_id=der_id, req_body=req_body
        )

        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "ACCEPTED"

        resp = client.delete("/api/contract/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        resp = client.get("/api/contract")
        assert resp.json[0]["contract_status"] == "USER_CANCELLED"

        resp = client.post("/api/enrollment", json=req_body["enrollment_body"])
        assert (
            resp.json[0]["message"]
            == "Contract already exists for this program, service provider, and der"
        )
        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "USER_CANCELLED"

    def test_cannot_update_contract_if_previously_cancelled(self, client, db_session):
        """BDD PM-1318

        Given the user is program admin
        And there is a service provider in the system
        And there is a der in the system which is assciated with the service provider
        And there is an accepted enrollement in the system which has created a contract
        When user has delete the contract
        And the contracts become user_cancelled
        And the user submit submit PATCH request to /api/contact/1 to update the contract
        Then user receive the message that the contract cannot be updated
        """
        der_id = "test_der"
        req_body = self._gen_raw_data(der_id)
        resp_body = self._create_prog_SP_DerAssoc_enrollment(  # noqa: F841
            client=client, der_id=der_id, req_body=req_body
        )

        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "ACCEPTED"

        resp = client.delete("/api/contract/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        resp = client.get("/api/contract")
        assert resp.json[0]["contract_status"] == "USER_CANCELLED"

        resp = client.post("/api/enrollment", json=req_body["enrollment_body"])
        assert (
            resp.json[0]["message"]
            == "Contract already exists for this program, service provider, and der"
        )
        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "USER_CANCELLED"

        resp = client.post("/api/enrollment", json=req_body["enrollment_body"])
        assert (
            resp.json[0]["message"]
            == "Contract already exists for this program, service provider, and der"
        )
        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "USER_CANCELLED"

        resp = client.post("/api/enrollment", json=req_body["enrollment_body"])
        assert (
            resp.json[0]["message"]
            == "Contract already exists for this program, service provider, and der"
        )
        resp = client.get("/api/contract")
        assert len(resp.json) == 1
        assert resp.json[0]["contract_status"] == "USER_CANCELLED"
