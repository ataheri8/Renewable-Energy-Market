import pytest

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.derinfo.repository import DerInfoRepository, DerNotFound, DerUpdate
from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.tests import factories


@pytest.fixture
def service_provider():
    sp = factories.ServiceProviderFactory()

    return sp


class TestDerInfoRepository:
    def _generate_ders(self, db_session, service_provider):
        factories.DerFactory(
            id=1,
            service_provider_id=service_provider.id,
            der_id="123",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.123,
            name="test_1",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        ),
        factories.DerFactory(
            id=2,
            service_provider_id=service_provider.id,
            der_id="234",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.2345,
            name="test_2",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        ),
        factories.DerFactory(
            id=3,
            der_id="345",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.01,
            name="test_3",
            is_deleted=True,
            resource_category=DerResourceCategory.GENERIC,
        )
        factories.DerFactory(
            id=4,
            der_id="456",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.1,
            name="test_3",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        )

    def test_get_ders_no_service_provider_is_deleted_false(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            got = DerInfoRepository(session).get_ders()
        assert got is not None
        assert len(got) == 3

    def test_get_ders_service_provider_is_deleted_false(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            got = DerInfoRepository(session).get_ders(service_provider=service_provider.id)
        assert got is not None
        assert len(got) == 2

    def test_get_ders_no_service_provider_is_deleted_true(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            got = DerInfoRepository(session).get_ders(is_deleted=True)
        assert got is not None
        assert len(got) == 1

    def test_get_ders_service_provider_is_deleted_true(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            got = DerInfoRepository(session).get_ders(
                service_provider=service_provider.id, is_deleted=True
            )
        assert got is not None
        assert len(got) == 0

    def test_get_der_id_none_der_id(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            der = DerInfoRepository(session).get_der()
        assert der is None

    def test_get_der_id(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            der = DerInfoRepository(session).get_der(der_id="123")
        assert der.der_id == "123"
        assert der.name == "test_1"

    def test_get_id(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            der = DerInfoRepository(session).get_der(id=1)
        assert der.id == 1
        assert der.name == "test_1"

    def test_get_id_with_sp(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            der = DerInfoRepository(session).get_der(id=1, service_provider=service_provider.id)
        assert der.id == 1
        assert der.name == "test_1"
        assert der.service_provider_id == service_provider.id

    def test_get_der_id_deleted_fail(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            der = DerInfoRepository(session).get_der(der_id="123", is_deleted=True)
        assert der is None

    def test_get_der_id_deleted(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            der = DerInfoRepository(session).get_der(der_id="345", is_deleted=True)
        assert der.der_id == "345"
        assert der.is_deleted is True

    def test_upsert_no_ders(self, db_session, service_provider):
        payload = DerUpdate(
            der_id="1ca6171e-1c30-4069-bdac-128022400328",
            name="_der_name",
            der_type="DR",
            resource_category="VPP",
            nameplate_rating=1,
            nameplate_rating_unit="MW",
            is_deleted=False,
            extra={"some": "data"},
        )
        with db_session() as session:
            DerInfoRepository(session).upsert_der_from_kafka(payload)
            session.commit()
            ders = DerInfoRepository(session).get_ders()
        assert len(ders) == 1
        assert ders[0].der_id == "1ca6171e-1c30-4069-bdac-128022400328"

    def test_upsert_existing_der(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        payload = DerUpdate(
            der_id="123",
            name="upsert_der_name",
            der_type="DR",
            resource_category="VPP",
            nameplate_rating=1,
            nameplate_rating_unit="MW",
            is_deleted=False,
            extra={"some": "data"},
        )

        with db_session() as session:
            DerInfoRepository(session).upsert_der_from_kafka(payload)
            session.commit()
            der = DerInfoRepository(session).get_der(der_id="123")
        assert der is not None
        assert der.name == "upsert_der_name"

    def test_upsert_existing_der_delete(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            # Get values before Upsert
            der = DerInfoRepository(session).get_der(der_id="123")
            assert der is not None
            assert der.name == "test_1"
            assert der.is_deleted is False
            assert der.service_provider_id is not None

        payload = {
            "der_id": "123",
            "name": "upsert_der_name",
            "der_type": "DR",
            "resource_category": "VPP",
            "nameplate_rating": 1,
            "nameplate_rating_unit": "MW",
            "is_deleted": True,
            "extra": {"some": "data"},
        }
        payload = DerUpdate(
            der_id="123",
            name="upsert_der_name",
            der_type="DR",
            resource_category="VPP",
            nameplate_rating=1,
            nameplate_rating_unit="MW",
            is_deleted=True,
            extra={"some": "data"},
        )
        DerInfoRepository(session).upsert_der_from_kafka(payload)
        session.commit()
        der = DerInfoRepository(session).get_der(der_id="123", is_deleted=True)
        assert der is not None
        assert der.name == "upsert_der_name"
        assert der.is_deleted is True
        assert der.service_provider_id is None

    def test_get_der_or_raise_exception(self, db_session):
        with pytest.raises(DerNotFound) as error:
            with db_session() as session:
                DerInfoRepository(session).get_der_or_raise_exception(id=1)

        assert error.value.args[0] == "DER was not found"

    def test_get_der_with_no_sp(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)
        with db_session() as session:
            ders = DerInfoRepository(session).get_ders_with_no_sp()
        assert ders is not None
        assert len(ders) == 1
        assert ders[0].service_provider_id is None

    def test_get_ders_with_sp_no_contract(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)

        enrollment_request_id = 1
        factories.EnrollmentRequestFactory(id=enrollment_request_id)
        factories.ContractFactory(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=service_provider.id,
            der_id="123",
        )
        with db_session() as session:
            ders = DerInfoRepository(session).get_ders_with_sp_no_contract()

        assert ders is not None
        assert len(ders) == 2
        for d in ders:
            assert d.der_id in ["123", "234"]

    def test_get_ders_with_sp_no_contract_in_program(self, db_session, service_provider):
        der = factories.DerFactory(service_provider_id=service_provider.id)
        der2 = factories.DerFactory(service_provider_id=service_provider.id)
        program = factories.ProgramFactory()
        enrollment = factories.EnrollmentRequestFactory(der=der, program=program)
        program2 = factories.ProgramFactory()
        enrollment2 = factories.EnrollmentRequestFactory(der=der2, program=program2)
        factories.ContractFactory(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            program=program,
            service_provider=service_provider,
            der=der,
            enrollment_request=enrollment,
        )
        factories.ContractFactory(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            program=program2,
            service_provider=service_provider,
            der=der2,
            enrollment_request=enrollment2,
        )
        with db_session() as session:
            ders = DerInfoRepository(session).get_ders_with_sp_no_contract()

        assert ders is not None
        assert len(ders) == 2
        assert der.der_id in [ders[0].der_id, ders[1].der_id]
        assert der2.der_id in [ders[0].der_id, ders[1].der_id]

    def test_upsert_der_invalid_float_nameplate_rating(self, db_session):
        new_value = 99.9876123
        payload = DerUpdate(
            der_id="123",
            name="upsert_der_name",
            der_type="DR",
            resource_category="VPP",
            nameplate_rating=new_value,
            nameplate_rating_unit="MW",
            is_deleted=False,
            extra={"some": "data"},
        )
        with db_session() as session:
            DerInfoRepository(session).upsert_der_from_kafka(payload)
            session.commit()
            ders = DerInfoRepository(session).get_ders()
        assert len(ders) == 1
        assert ders[0].der_id == "123"
        assert type(ders[0].nameplate_rating) == float
        assert ders[0].nameplate_rating == round(payload.nameplate_rating, 4)
