import json
from http import HTTPStatus

import pytest

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


# TODO find the BDDs for this
class TestServiceProvider(TestDataMixin):
    @pytest.mark.skip(reason="end2end currently not implemented")
    def test_negative_scenario_create_der_association_bad_columns(
        self, client, db_session
    ) -> None:  # noqa E501
        # Create Service Provider

        filepath_sp = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filepath_sp, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Test with invalid data

        filepath_assoc = self._get_test_data_path(
            "invalid_service_provider_der_association_bad_columns.csv"
        )
        body = open(filepath_assoc, "rb")
        resp = client.post(
            "/api/serviceprovider/1/upload",
            data=body,
            headers={"Content-Type": "text/csv"},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert resp.json["message"] == "Invalid Column Type must be 'der_rdf_id'"

    @pytest.mark.skip(reason="end2end currently not implemented")
    def test_complete_scenario_create_der_association_bad_data(self, client, db_session) -> None:
        # Create Service Provider

        filepath_sp = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filepath_sp, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Create DER's to associate with

        # Valid uuid, with service provider

        factories.DerFactory(
            der_id="1ca6171e-1c30-4069-bdac-128022400328",
            name="test_1",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
            service_provider_id=1,
        )

        # Valid uuid, no service provider

        factories.DerFactory(
            der_id="c77b2af4-aa6a-402c-b9e3-115fe55ee00d",
            name="test_1",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )

        # Test with valid data, with one row being non-existing DER UUID

        filepath_assoc = self._get_test_data_path("valid_service_provider_der_association.csv")
        body = open(filepath_assoc, "rb")
        resp = client.post(
            "/api/serviceprovider/1/upload",
            data=body,
            headers={"Content-Type": "text/csv"},
        )

        assert resp.status_code == HTTPStatus.CREATED
        # Message for a good one
        assert resp.json[0]["outcome"] == "Associated to service provider with id 1"
        # Message for a failed one due to already being associated
        assert resp.json[1]["outcome"] == "could not associated to service provider with id 1"
        assert (
            resp.json[1]["reason"]
            == "No DER found with rdf_id 1ca6171e-1c30-4069-bdac-128022400328 or it is already associated with a different service provider."  # noqa E501
        )
        # Message for a failed one due to no such DER
        assert resp.json[2]["outcome"] == "could not associated to service provider with id 1"
        assert (
            resp.json[2]["reason"]
            == "No DER found with rdf_id 0ad50b31-ce90-41bf-8441-0e72ea5c9295 or it is already associated with a different service provider."  # noqa E501
        )

    def test_negative_scenario_delete_der_association(self, client, db_session) -> None:
        # Create Service Provider

        filepath_sp = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filepath_sp, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Create DER with an association

        factories.DerFactory(
            der_id="1ca6171e-1c30-4069-bdac-128022400328",
            name="test_1",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
            service_provider_id=1,
        )

        # Test Deleting DER Association

        resp = client.delete("/api/serviceprovider/1/123")

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert (
            resp.json["message"]
            == "Association of Service Provider with id 1 with Der with id 123 is not found"
        )

    def test_negative_scenario_delete_der_association_association_with_another_service_provider(
        self, client, db_session
    ) -> None:
        # Create Service Provider

        filepath_sp = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filepath_sp, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Create another Service Provider

        body["general_fields"]["name"] = "ABC_" + body["general_fields"]["name"]
        body["primary_contact"]["email_address"] = (
            "ABC_" + body["primary_contact"]["email_address"]
        )  # noqa E501
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Create DER with an association

        factories.DerFactory(
            der_id="1ca6171e-1c30-4069-bdac-128022400328",
            name="test_1",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
            service_provider_id=1,
        )

        # Test Deleting DER Association

        resp = client.delete("/api/serviceprovider/2/1")

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert (
            resp.json["message"].lower()
            == "Association of Service Provider with id 2 with Der with id 1 is not found".lower()
        )

    def test_negative_scenario_delete_der_association_service_provider_not_found(
        self, client, db_session
    ) -> None:
        # Test Deleting DER Association

        resp = client.delete("/api/serviceprovider/1/1")

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert resp.json["message"].lower() == "Service Provider with id 1 is not found".lower()

    def test_negative_scenario_delete_der_association_association_already_deleted(
        self, client, db_session
    ) -> None:
        # Create Service Provider

        filepath_sp = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filepath_sp, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Create DER with no association

        factories.DerFactory(
            id=1,
            der_id="1ca6171e-1c30-4069-bdac-128022400328",
            name="test_1",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
            service_provider_id=1,
        )

        # Test Deleting DER Association

        resp = client.delete("/api/serviceprovider/1/1")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        # Test Deleting again DER Association

        resp = client.delete("/api/serviceprovider/1/1")

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert (
            resp.json["message"].lower()
            == "Association of Service Provider with id 1 with Der with id 1 is not found".lower()
        )

    def test_positive_scenario_delete_der_association(self, client, db_session) -> None:
        # Create Service Provider

        filepath_sp = self._get_test_data_path("valid_service_provider_data_all_fields.json")
        with open(filepath_sp, "r") as file:
            body = json.load(file)
        resp = client.post(
            "/api/serviceprovider/", headers={"Content-Type": "application/json"}, json=body
        )
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.response is not None

        # Create DER with an association

        factories.DerFactory(
            id=1,
            der_id="1ca6171e-1c30-4069-bdac-128022400328",
            name="test_1",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
            service_provider_id=1,
        )

        # Test Deleting DER Association

        resp = client.delete("/api/serviceprovider/1/1")

        assert resp.status_code == HTTPStatus.NO_CONTENT
