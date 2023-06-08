import pytest

from pm.modules.derinfo.controller import DerInfoController
from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.tests import factories


@pytest.fixture
def service_provider():
    sp = factories.ServiceProviderFactory()

    return sp


class TestDerInfoController:
    def _generate_ders(self, db_session, service_provider):
        factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id="123",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.235,
            name="test_1",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        ),
        factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id="234",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.45,
            name="test_2",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        ),
        factories.DerFactory(
            der_id="345",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.8932,
            name="test_3",
            is_deleted=True,
            resource_category=DerResourceCategory.GENERIC,
        )
        factories.DerFactory(
            der_id="456",
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            nameplate_rating=100.12,
            name="test_3",
            is_deleted=False,
            resource_category=DerResourceCategory.GENERIC,
        )

    def test_get_available_ders_not_in_program(self, db_session, service_provider):
        self._generate_ders(db_session, service_provider)

        enrollment_request_id = 1
        der1 = factories.DerFactory()
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der1)
        factories.ContractFactory(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=service_provider.id,
            der_id=der1.der_id,
        )

        ders = DerInfoController().get_available_ders_not_in_program(program_id=1)

        assert ders is not None
        assert len(ders) == 2
        for d in ders:
            assert d.der_id in ["123", "234"]
