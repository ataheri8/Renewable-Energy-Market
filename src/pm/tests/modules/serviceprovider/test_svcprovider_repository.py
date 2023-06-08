from uuid import uuid4

import pytest

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.modules.serviceprovider.models.service_provider import ServiceProvider
from pm.modules.serviceprovider.repository import (
    ServiceProviderDerAssociationNotFound,
    ServiceProviderNotFound,
    ServiceProviderRepository,
)
from pm.tests import factories


@pytest.fixture
def service_provider():
    sp = factories.ServiceProviderFactory()
    sp.ders = [
        DerInfo(
            service_provider_id=sp.id,
            der_id=f"{uuid4()}",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100,
            name="test_1",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        )
    ]
    return sp


class TestServiceProviderRepository:
    def _get_all_ders(self, db_session) -> list[DerInfo]:
        with db_session() as session:
            return session.query(DerInfo).all()

    def test_save(self, db_session):
        with db_session() as session:
            service_provider_id = 1
            repo = ServiceProviderRepository(session)
            service_provider = repo.get_service_provider(service_provider_id)
            assert service_provider is None
            service_provider = ServiceProvider(
                id=service_provider_id,
                name="test",
                uuid=f"{uuid4()}",
                service_provider_type=ServiceProviderType.AGGREGATOR,
                status=ServiceProviderStatus.ACTIVE,
                primary_contact=dict(
                    email_address="mlh@ge.com",
                    phone_number="905-444-5566",
                ),
                notification_contact=dict(
                    email_address="JohnDoe@ge.com",
                    phone_number="905-334-7766",
                ),
                address=dict(
                    street="123 Which Street",
                    city="NoCity",
                    state="NoState",
                    country="NoCountry",
                    zip_code="A1B2C3",
                    apt_unit="123",
                ),
            )
            repo.save(service_provider)
            session.commit()
            service_provider = repo.get_service_provider(service_provider_id)
            assert service_provider is not None

    def test_get_all(self, db_session):
        factories.ServiceProviderFactory()
        factories.ServiceProviderFactory()
        with db_session() as session:
            got = ServiceProviderRepository(session).get_all()
        expected = 2
        assert len(got) == expected

    def test_get_all_with_ders(self, db_session):
        sp_1 = factories.ServiceProviderFactory()
        sp_2 = factories.ServiceProviderFactory()
        factories.DerFactory(der_id="der1_id", service_provider_id=sp_1.id, is_deleted=False)
        factories.DerFactory(der_id="der2_id", service_provider_id=sp_2.id, is_deleted=True)
        with db_session() as session:
            got = ServiceProviderRepository(session).get_all()
        expected = 2
        assert len(got) == expected

    def test_get(self, db_session, service_provider):
        with db_session() as session:
            got = ServiceProviderRepository(session).get_service_provider(service_provider.id)
        assert got is not None

    def test_get_with_ders(self, db_session, service_provider):
        factories.DerFactory(
            der_id="der1_id", service_provider_id=service_provider.id, is_deleted=False
        )
        factories.DerFactory(
            der_id="der2_id", service_provider_id=service_provider.id, is_deleted=True
        )
        with db_session() as session:
            got = ServiceProviderRepository(session).get_service_provider(service_provider.id)
        assert got is not None

    def test_update_der(self, db_session, service_provider):
        der1 = factories.DerFactory(
            der_id="der1_id", service_provider_id=service_provider.id, is_deleted=False
        )
        der2 = factories.DerFactory(der_id="der2_id", service_provider_id=None, is_deleted=False)
        with db_session() as session:
            with pytest.raises(ServiceProviderDerAssociationNotFound):
                ServiceProviderRepository(session).update_der(service_provider.id, der2.der_id)
                ServiceProviderRepository(session).update_der(service_provider.id, der1.der_id)

    def test_get_der_with_uuid(self, db_session, service_provider):
        der1 = factories.DerFactory(
            der_id="der1_id", service_provider_id=service_provider.id, is_deleted=False
        )
        with db_session() as session:
            got = ServiceProviderRepository(session).get_der_with_uuid(
                service_provider.id, der1.der_id
            )
        assert got is not None

    def test_get_or_raise(self, db_session, service_provider):
        with db_session() as session:
            got = ServiceProviderRepository(session).get_service_provider_or_raise(
                service_provider.id
            )
        assert got is not None

    def test_get_or_raise_fail(self, db_session):
        with pytest.raises(ServiceProviderNotFound):
            with db_session() as session:
                ServiceProviderRepository(session).get_service_provider_or_raise(1)

    def test_get_der(self, db_session, service_provider):
        der_id = service_provider.ders[0].id
        with db_session() as session:
            got = ServiceProviderRepository(session).get_der(service_provider.id, der_id)
        assert got is None

    def test_get_der_or_raise_fail(self, db_session, service_provider):
        service_provider_id = service_provider.id
        with pytest.raises(ServiceProviderDerAssociationNotFound):
            with db_session() as session:
                ServiceProviderRepository(session).get_der_or_raise(service_provider_id, 999999)

    def test_get_ders_service_provider(self, db_session, service_provider):
        with db_session() as session:
            got = ServiceProviderRepository(session).get_ders_service_provider(service_provider.id)
        assert len(got) == 1

    def test_get_der_without_serviceprovider(self, db_session):
        der_id = f"{uuid4()}"
        factories.DerFactory(
            der_id=der_id,
            name="test",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )
        with db_session() as session:
            got = ServiceProviderRepository(session).get_der_without_serviceprovider(der_id)
        assert got is not None
