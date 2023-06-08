from http import HTTPStatus

import pytest

from pm.modules.serviceprovider.enums import ServiceProviderStatus
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


class TestPM1115(TestDataMixin):
    """
    https://opusonesolutions.atlassian.net/browse/PM-1115
    Associate DERs to a ServiceProvider using JSON payload
    """

    @pytest.fixture
    def der_payload(self):
        der_id_list = []
        for _ in range(0, 3):
            der = factories.DerFactory()
            _dict = {"der_id": der.der_id}
            der_id_list.append(_dict)
        return der_id_list

    def test_positive_service_provider_der_association(self, client, db_session, der_payload):
        """
        BDD Scenario: PM-1116
        Given a service provider is in the system
        When user send POST request on url
        "/api/serviceprovider/<service_provider_id>/associate_ders" to
            asscoiate DER to service provider
        And DER is availale in the derwh.
        Then user should succesfully able to associate DER with service provider.
        And get success response.
        """
        service_provider = factories.ServiceProviderFactory()
        resp = client.post(
            f"/api/serviceprovider/{service_provider.id}/associate_ders",
            json=der_payload,
        )
        assert resp.status_code == HTTPStatus.OK
        print(resp.json)
        actual_list = []
        for r in resp.json:
            actual_list.append(r["der_id"])
        for der in der_payload:
            assert der["der_id"] in actual_list

    def test_invalid_der_service_provider_der_association(self, client, db_session):
        """
        BDD Scenario: PM-1117
        Given a service provider is in the system
        When user send POST request on url
        "/api/serviceprovider/<service_provider_id>/associate_ders" to
            asscoiate DER to service provider
        And DER is not available in derwh.
        Then user should get response saying DER not found derwh.
        And get error response.
        """
        service_provider = factories.ServiceProviderFactory()
        der = factories.DerFactory()
        resp = client.post(
            f"/api/serviceprovider/{service_provider.id}/associate_ders",
            json=[{"der_id": "non_existent_der_id"}, {"der_id": der.der_id}],
        )
        assert resp.json[0]["status_code"] == 4  # status code 4 means der is not in system
        assert resp.json[1]["status_code"] == 3  # status code 3 means der is associated

    def test_inactive_service_provider_der_association(self, client, db_session):
        """
        BDD Scenario PM-1339:
        Given a service provider is in the system but inactive
        When user send POST request on url
        "/api/serviceprovider/<service_provider_id>/associate_ders" to
            asscoiate DER to service provider
        And DER is available in derwh.
        Then user should get response saying the service provider is inactive.
        And get error response.
        """
        service_provider = factories.ServiceProviderFactory(status=ServiceProviderStatus.INACTIVE)
        der = factories.DerFactory()
        resp = client.post(
            f"/api/serviceprovider/{service_provider.id}/associate_ders",
            json=[{"der_id": der.der_id}],
        )
        assert "not active" in resp.json["message"]  # status code 4 means der is not in system

    def test_invalid_servicer_provider_der_association(self, client, db_session, der_payload):
        """
        BDD Scenario: PM-1118
        Given a service provider is not in the system
        When user send POST request on url
        "/api/serviceprovider/<service_provider_id>/associate_ders" to
            asscoiate DER to service provider
        And DER is availale in the derwh.
        Then user should get response saying service provider not available.
        And get an error response.
        """
        resp = client.post(
            "/api/serviceprovider/2/associate_ders",
            json=der_payload,
        )
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_duplicate_der_id(self, client, db_session):
        service_provider = factories.ServiceProviderFactory()
        der_1 = factories.DerFactory()
        der_2 = factories.DerFactory()
        der_payload = [{"der_id": der_1.der_id}, {"der_id": der_1.der_id}, {"der_id": der_2.der_id}]
        resp = client.post(
            f"/api/serviceprovider/{service_provider.id}/associate_ders",
            json=der_payload,
        )

        assert resp.json[0]["status_code"] == 3  # status code 3 means der is associated

        # checking that second der_id which is duplicate gets denied and does not get associated
        assert resp.json[1]["status_code"] == 1  # status code 1 means duplicate der_id
        assert resp.json[1]["reason"] == "Duplicate der_id"

        assert resp.json[2]["status_code"] == 3  # status code 3 means der is associated

    def test_invalid_data_in_json(self, client, db_session):
        service_provider = factories.ServiceProviderFactory()
        invalid_payload_1 = [{"invalid_key": "invalid_der_id"}]
        resp_1 = client.post(
            f"/api/serviceprovider/{service_provider.id}/associate_ders",
            json=invalid_payload_1,
        )
        assert resp_1.json["code"] == HTTPStatus.UNPROCESSABLE_ENTITY

        invalid_payload_2 = [{"der_id": ""}]
        resp_2 = client.post(
            f"/api/serviceprovider/{service_provider.id}/associate_ders",
            json=invalid_payload_2,
        )

        assert resp_2.json[0]["status_code"] == 2  # status code 2 invalid format or missing der_id
        assert resp_2.json[0]["reason"] == "Either incorrect format, values or missing der_id"
