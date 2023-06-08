from http import HTTPStatus

import pytest

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.tests import factories


@pytest.fixture
def service_provider():
    sp = factories.ServiceProviderFactory()

    return sp


class TestPM321:
    def _generate_ders(self, db_session, service_provider):
        factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id="123",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100,
            name="test_1",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        ),
        factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id="234",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100,
            name="test_2",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        ),
        factories.DerFactory(
            der_id="345",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100,
            name="test_3",
            is_deleted=True,
            resource_category=DerResourceCategory.GENERIC,
        )
        factories.DerFactory(
            der_id="456",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100,
            name="test_3",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        )

    def test_get_available_ders(self, client, db_session, service_provider) -> None:
        """BDD PM-782

        Given many DERS
        When Ders have service provider
        And Ders are not deleted
        And Ders are not in a contract
        Then return list of DERS
        """
        # Setup environment

        der = factories.DerFactory(service_provider_id=service_provider.id)
        der2 = factories.DerFactory(service_provider_id=service_provider.id)
        enrollment_request_id = 1
        enrollment = factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        factories.ContractFactory(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program=enrollment.program,
            service_provider=service_provider,
            der=der,
        )

        resp = client.get("/api/der/available_ders")
        assert resp.status_code == HTTPStatus.OK
        assert resp.response is not None
        assert len(resp.json) == 2
        assert der2.der_id in [resp.json[0]["der_id"], resp.json[1]["der_id"]]
        assert der.der_id in [resp.json[0]["der_id"], resp.json[1]["der_id"]]

        resp = client.get("/api/program/1/available_ders")
        assert resp.status_code == HTTPStatus.OK
        assert resp.response is not None
        assert len(resp.json) == 1
        assert resp.json[0]["der_id"] == der2.der_id

    def test_get_available_ders_no_contract(self, client, db_session, service_provider) -> None:
        """BDD PM-783

        Given many DERS
        When Ders have no service provider
        And Ders are not deleted
        And Ders are not in a contract
        Then return list of DERS
        """

        # Setup environment

        self._generate_ders(db_session, service_provider)
        enrollment_request_id = 1
        factories.EnrollmentRequestFactory(id=enrollment_request_id)

        resp = client.get("/api/der/available_ders")
        assert resp.status_code == HTTPStatus.OK
        assert resp.response is not None
        assert len(resp.json) == 2
        for der_id in resp.json:
            assert der_id["der_id"] in ["123", "234"]

    def test_get_non_associated_ders(self, client, db_session, service_provider) -> None:
        # Setup environment

        self._generate_ders(db_session, service_provider)

        resp = client.get("/api/der/non_associated_ders")
        assert resp.status_code == HTTPStatus.OK
        assert resp.response is not None
        assert len(resp.json) == 1
        assert resp.json[0]["der_id"] == "456"

    def test_get_non_associated_ders_none_found(self, client, db_session, service_provider) -> None:
        # Setup environment

        factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id="234",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100,
            name="test_2",
            is_deleted=True,
            resource_category=DerResourceCategory.GENERIC,
        ),

        resp = client.get("/api/der/non_associated_ders")
        assert resp.status_code == HTTPStatus.OK
        assert resp.response is not None
        assert len(resp.json) == 0
