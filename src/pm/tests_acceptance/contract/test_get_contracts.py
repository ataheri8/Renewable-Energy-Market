from http import HTTPStatus

from pm.tests import factories


class TestGetContract:
    def test_get_all_contract(self, client, db_session):
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 0
        factories.ContractFactory(id=1)
        resp = client.get("/api/contract/")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json) == 1
        assert resp.json[0]["id"] == 1
        assert resp.json[0]["der"] is not None
        assert resp.json[0]["program"] is not None
        assert resp.json[0]["service_provider"] is not None

    def test_get_contract(self, client, db_session):
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["id"] == contract_id
        assert resp.json["der"] is not None
        assert resp.json["program"] is not None
        assert resp.json["service_provider"] is not None

    def test_get_non_existing_contract(self, client, db_session):
        resp = client.get("/api/contract/1")
        assert resp.status_code == HTTPStatus.NOT_FOUND
