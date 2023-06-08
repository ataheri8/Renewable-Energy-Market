import pendulum
import pytest as pytest
from sqlalchemy import select

from pm.consumers.der_warehouse import handlers
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.derinfo.repository import DerUpdate
from pm.modules.enrollment.enums import ContractStatus
from pm.modules.enrollment.models.enrollment import Contract
from pm.tests import factories


@pytest.fixture
def der_deleted_data():
    """Example payload from DER Warehouse der topic"""
    data = {
        "id": 1,
        "der_id": "deleted_der_id",
        "name": "deleted_der",
        "der_type": "WIND_FARM",
        "resource_category": "GENERIC",
        "nameplate_rating": 50,
        "nameplate_rating_unit": "kW",
        "is_deleted": True,
        "extra": {"somedata": "hi"},
        "created_at": str(pendulum.now()),
        "updated_at": str(pendulum.now()),
    }
    return DerUpdate.from_dict(data)


class TestPM438:
    def test_der_deleted_with_no_contracts(self, der_deleted_data, db_session):
        """
        PM-1002
        Given a DER has no contracts in PM
        When that DER is removed from DER warehouse
        Then no contracts are modified
        """
        der_id = "deleted_der_id"
        other_der_id = "other_der_id"
        sp = factories.ServiceProviderFactory()
        factories.DerFactory(der_id=der_id, service_provider_id=sp.id, is_deleted=False)
        der = factories.DerFactory(der_id=other_der_id, service_provider_id=sp.id, is_deleted=False)
        factories.ContractFactory(id=1, contract_status=ContractStatus.ACTIVE, der=der)
        factories.ContractFactory(id=2, contract_status=ContractStatus.ACCEPTED, der=der)
        handlers.handle_derwh_der(der_deleted_data)

        with db_session() as session:
            stmt = select(DerInfo).where(DerInfo.der_id == other_der_id)
            not_updated_der = session.execute(stmt).unique().scalar_one_or_none()
            assert not_updated_der is not None
            assert not_updated_der.is_deleted is False
            assert not_updated_der.service_provider_id is not None
            stmt = select(Contract).where(Contract.der_id == other_der_id)
            not_updated_contracts = session.execute(stmt).unique().scalars().all()
            for c in not_updated_contracts:
                assert c.contract_status != ContractStatus.SYSTEM_CANCELLED

    def test_der_deleted_with_active_accepted_contracts(self, der_deleted_data, db_session):
        """
        PM-1003
        Given a DER has contracts in PM
        And those contracts have a status of ACTIVE or ACCEPTED or USER_CANCELLED
        When that DER is removed from DER warehouse
        Then those contracts will have their status changed to SYSTEM_CANCELLED
        """
        der_id = "deleted_der_id"
        sp = factories.ServiceProviderFactory()
        der = factories.DerFactory(der_id=der_id, service_provider_id=sp.id, is_deleted=False)
        factories.ContractFactory(id=1, contract_status=ContractStatus.ACTIVE, der=der)
        factories.ContractFactory(id=2, contract_status=ContractStatus.ACCEPTED, der=der)
        handlers.handle_derwh_der(der_deleted_data)

        with db_session() as session:
            stmt = select(DerInfo).where(DerInfo.der_id == der_id)
            updated_der = session.execute(stmt).unique().scalar_one_or_none()
            assert updated_der is not None
            assert updated_der.is_deleted is True
            assert updated_der.service_provider_id is None
            stmt = select(Contract).where(Contract.der_id == der_id)
            updated_contracts = session.execute(stmt).unique().scalars().all()
            for c in updated_contracts:
                assert c.contract_status == ContractStatus.SYSTEM_CANCELLED

    def test_der_deleted_with_expired_cancelled_contracts(self, der_deleted_data, db_session):
        """
        PM-1004
        Given a DER has contracts in PM
        And those contracts have a status of EXPIRED or SYSTEM_CANCELLED
        When that DER is removed from DER warehouse
        Then those contracts will not have their status changed
        """
        der_id = "deleted_der_id"
        sp = factories.ServiceProviderFactory()
        der = factories.DerFactory(der_id=der_id, service_provider_id=sp.id, is_deleted=False)
        contract_1 = factories.ContractFactory(
            id=1, contract_status=ContractStatus.EXPIRED, der=der
        )
        contract_2 = factories.ContractFactory(
            id=2, contract_status=ContractStatus.SYSTEM_CANCELLED, der=der
        )
        contract_1_id = contract_1.id
        contract_2_id = contract_2.id
        handlers.handle_derwh_der(der_deleted_data)

        with db_session() as session:
            stmt = select(DerInfo).where(DerInfo.der_id == der_id)
            updated_der = session.execute(stmt).unique().scalar_one_or_none()
            assert updated_der is not None
            assert updated_der.is_deleted is True
            assert updated_der.service_provider_id is None

            stmt = select(Contract).where(Contract.id == contract_1_id)
            contract_1 = session.execute(stmt).unique().scalar_one()
            assert contract_1.contract_status == ContractStatus.EXPIRED
            assert contract_1.der_id == der_id

            stmt = select(Contract).where(Contract.id == contract_2_id)
            contract_2 = session.execute(stmt).unique().scalar_one()
            assert contract_2.contract_status == ContractStatus.SYSTEM_CANCELLED
            assert contract_2.der_id == der_id
