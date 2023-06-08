from http import HTTPStatus
from uuid import uuid4

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.serviceprovider.controller import ServiceProviderController
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


class TestPM612(TestDataMixin):
    """As a user, I need to be able to download associated DERs for a service provider as a csv"""

    def test_download_service_provider_associated_der_csv(self, client, db_session):
        """BDD PM-613
        Given An utility access the endpoint
              GET /api/serviceprovider/<serviceprovider-id>/download_data
        Then the user gets a csv file
        And the csv file includes a list of associated DERs and its data
        """
        factories.ServiceProviderFactory(id=1)
        der_uuid_1, der_uuid_2 = f"{uuid4()}", f"{uuid4()}"
        factories.DerFactory(
            der_id=der_uuid_1,
            name="test",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )

        factories.DerFactory(
            der_id=der_uuid_2,
            name="test2",
            nameplate_rating=120,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.WIND_FARM,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )
        der_object_1 = dict(
            der_id=der_uuid_1,
        )
        der_object_2 = dict(
            der_id=der_uuid_2,
        )
        ServiceProviderController().associate_ders(1, [der_object_1, der_object_2])
        resp = client.get("api/serviceprovider/1/download_data")
        assert resp.status_code == HTTPStatus.OK
        output_data = resp.data.decode("utf-8-sig")
        assert der_uuid_1 in output_data
        assert der_uuid_2 in output_data

    def test_download_service_provider_associated_der_invalid_id(self, client, db_session):
        resp = client.get("api/serviceprovider/999999/download_data")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_download_service_provider_associated_der_no_association_found(
        self, client, db_session
    ):
        factories.ServiceProviderFactory(id=1)
        resp = client.get("api/serviceprovider/1/download_data")
        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert resp.json["message"] == "no DERs are associated with service provider id 1"
