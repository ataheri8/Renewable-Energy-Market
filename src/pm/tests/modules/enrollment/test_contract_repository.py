import pytest

from pm.modules.enrollment.contract_repository import (
    ContractNotFound,
    ContractRepository,
)
from pm.modules.enrollment.enums import (
    ContractKafkaOperation,
    ContractStatus,
    ContractType,
)
from pm.modules.enrollment.models.enrollment import Contract
from pm.tests import factories


class TestContractRepository:
    def _get_all_contract(self, db_session) -> list[Contract]:
        with db_session() as session:
            return session.query(Contract).all()

    def test_get_all(self, db_session):
        num_of_contract = 5
        for _ in range(num_of_contract):
            factories.ContractFactory()
        with db_session() as session:
            contracts = ContractRepository(session).get_all()
        assert len(contracts) == num_of_contract

        with db_session() as session:
            contracts = ContractRepository(session).get_all(eager_load=True)
        assert len(contracts) == num_of_contract
        for contract in contracts:
            assert contract is not None
            assert contract.id is not None
            assert contract.program is not None
            assert contract.der is not None
            assert contract.service_provider is not None

    @pytest.fixture
    def contract_setup(self, db_session):
        program = factories.ProgramFactory(id=1)
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der1,
        )
        factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
        )
        return der1

    @pytest.fixture
    def contract_setup_expired_cancelled(self, db_session):
        program_1 = factories.ProgramFactory(id=1)
        program_2 = factories.ProgramFactory(id=2)
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider_1,
            der=der1,
        )
        enrollment_request_2 = factories.EnrollmentRequestFactory(
            program=program_2,
            service_provider=service_provider_1,
            der=der1,
        )
        factories.ContractFactory(
            id=1,
            program=program_1,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
            contract_status=ContractStatus.EXPIRED,
        )
        factories.ContractFactory(
            id=2,
            program=program_2,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_2,
            der=der1,
            contract_status=ContractStatus.SYSTEM_CANCELLED,
        )
        return der1

    @pytest.mark.parametrize(
        "contract_exist",
        [
            pytest.param(True, id="one-contract"),
            pytest.param(False, id="zero-contract"),
        ],
    )
    def test_get(self, db_session, contract_exist):
        with db_session() as session:
            if contract_exist:
                factories.ContractFactory()
                contract_id = self._get_all_contract(db_session)[0].id
                contract = ContractRepository(session).get(contract_id)
                assert contract is not None
                assert contract.id == contract_id

                contract = ContractRepository(session).get(contract_id, eager_load=True)
                assert contract is not None
                assert contract.id == contract_id
                assert contract.program is not None
                assert contract.der is not None
                assert contract.service_provider is not None
            else:
                contract = ContractRepository(session).get(1)
                assert contract is None

    @pytest.mark.parametrize(
        "contract_exist",
        [
            pytest.param(True, id="one-contract"),
            pytest.param(False, id="zero-contract"),
        ],
    )
    def test_get_contract_or_raise(self, db_session, contract_exist):
        with db_session() as session:
            if contract_exist:
                factories.ContractFactory()
                contract_id = self._get_all_contract(db_session)[0].id
                contract = ContractRepository(session).get_contract_or_raise(contract_id)
                assert contract is not None
            else:
                with pytest.raises(ContractNotFound):
                    ContractRepository(session).get_contract_or_raise(1)

    def test_save_create_contract(self, db_session):
        # Create an enrollment & service-provider in the db for the contract
        enrollment_request_id = 1
        der = factories.DerFactory()
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        service_provider_id = 1
        factories.ServiceProviderFactory(id=service_provider_id)

        contract = Contract(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=1,
            der_id=der.der_id,
        )
        with db_session() as session:
            id = ContractRepository(session).save_create_contract(contract)
            session.commit()

        # TODO tests if kafka message has a header with field "operation:CREATED"

        contracts = self._get_all_contract(db_session)
        assert len(contracts) == 1
        assert contracts[0].id == id

    def test_save_update_contract(self, db_session):
        # Create an enrollment & service-provider in the db for the contract
        enrollment_request_id = 1
        der = factories.DerFactory()
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        service_provider_id = 1
        factories.ServiceProviderFactory(id=service_provider_id)

        contract = Contract(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=1,
            der_id=der.der_id,
        )
        with db_session() as session:
            id = ContractRepository(session).save_create_contract(contract)
            session.commit()
            contract = ContractRepository(session).get(id)
        assert contract.dynamic_operating_envelopes is None

        contract.dynamic_operating_envelopes = dict(
            default_limits_active_power_import_kw=0.0,
            default_limits_active_power_export_kw=0.0,
            default_limits_reactive_power_import_kw=0.0,
            default_limits_reactive_power_export_kw=0.0,
        )
        with db_session() as session:
            ContractRepository(session).save_update_contract(contract)
            session.commit()
            # TODO tests if kafka message has a header with field "operation:UPDATED"
            updated_contract = ContractRepository(session).get(id)

        assert updated_contract.dynamic_operating_envelopes
        assert (
            updated_contract.dynamic_operating_envelopes["default_limits_active_power_export_kw"]
            >= 0
        )
        assert (
            updated_contract.dynamic_operating_envelopes["default_limits_active_power_export_kw"]
            >= 0
        )
        assert (
            updated_contract.dynamic_operating_envelopes["default_limits_reactive_power_import_kw"]
            >= 0
        )
        assert (
            updated_contract.dynamic_operating_envelopes["default_limits_reactive_power_export_kw"]
            >= 0
        )

    def test_save_delete_contract(self, db_session):
        # Create an enrollment & service-provider in the db for the contract
        enrollment_request_id = 1
        der = factories.DerFactory()
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        service_provider_id = 1
        factories.ServiceProviderFactory(id=service_provider_id)

        contract = Contract(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=1,
            der_id=der.der_id,
        )
        with db_session() as session:
            id = ContractRepository(session).save_create_contract(contract)
            session.commit()
            contract = ContractRepository(session).get(id)
            assert contract.contract_status == ContractStatus.ACCEPTED
            contract.contract_status = ContractStatus.USER_CANCELLED

            ContractRepository(session).save_delete_contract(contract)
            session.commit()
            # TODO tests if kafka message has a header with field "operation:DELETED"

            deleted_contract = ContractRepository(session).get(id)
            assert deleted_contract.contract_status == ContractStatus.USER_CANCELLED

    def test_save_undo_delete_contract(self, db_session):
        # Create an enrollment & service-provider in the db for the contract
        enrollment_request_id = 1
        der = factories.DerFactory()
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        service_provider_id = 1
        factories.ServiceProviderFactory(id=service_provider_id)

        contract = Contract(
            contract_status=ContractStatus.USER_CANCELLED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=1,
            der_id=der.der_id,
        )
        with db_session() as session:
            id = ContractRepository(session).save_create_contract(contract)
            session.commit()
            contract = ContractRepository(session).get(id)
            assert contract.contract_status == ContractStatus.USER_CANCELLED
            contract.contract_status = ContractStatus.ACCEPTED

            ContractRepository(session).save_undo_delete_contract(contract)
            session.commit()
            # TODO tests if kafka message has a header with field "operation:REACTIVATED"

            undo_deleted_contract = ContractRepository(session).get(id)
            assert undo_deleted_contract.contract_status == ContractStatus.ACCEPTED

    def test_save_contract(self, db_session):
        # Create an enrollment & service-provider in the db for the contract
        enrollment_request_id = 1
        der = factories.DerFactory()
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        service_provider_id = 1
        factories.ServiceProviderFactory(id=service_provider_id)

        contract = Contract(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=enrollment_request_id,
            program_id=1,
            service_provider_id=1,
            der_id=der.der_id,
            der=der,
        )
        with db_session() as session:
            id = ContractRepository(session).save_contract(
                contract, operation=ContractKafkaOperation.CREATED
            )
            session.commit()
        contracts = self._get_all_contract(db_session)
        assert len(contracts) == 1
        assert contracts[0].id == id

    @pytest.mark.parametrize(
        "program_id,service_provider_id,der_id,contract_id,found",
        [
            pytest.param(1, 1, "der_1", 1, True, id="contract-1"),
            pytest.param(1, 2, "der_2", 2, True, id="contract-2"),
            pytest.param(1, 2, "der_3", 3, True, id="contract-3"),
            pytest.param(1, 2, "der_4", None, False, id="contract-none"),
        ],
    )
    def test_get_contract_by_unique_constraint(
        self,
        db_session,
        program_id,
        service_provider_id,
        der_id,
        contract_id,
        found,
    ):
        program = factories.ProgramFactory(id=1)
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        service_provider_2 = factories.ServiceProviderFactory(id=2)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der1,
        )
        der2 = factories.DerFactory(der_id="der_2", service_provider_id=service_provider_2.id)
        enrollment_request_2 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_2,
            der=der2,
        )
        der3 = factories.DerFactory(der_id="der_3", service_provider_id=service_provider_2.id)
        enrollment_request_3 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_2,
            der=der3,
        )
        factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
        )
        factories.ContractFactory(
            id=2,
            program=program,
            service_provider=service_provider_2,
            enrollment_request=enrollment_request_2,
            der=der2,
        )
        factories.ContractFactory(
            id=3,
            program=program,
            service_provider=service_provider_2,
            enrollment_request=enrollment_request_3,
            der=der3,
        )
        with db_session() as session:
            contract = ContractRepository(session).get_contract_by_unique_constraint(
                program_id,
                service_provider_id,
                der_id,
            )

        if found:
            assert contract.program_id == program_id
            assert contract.service_provider_id == service_provider_id
            assert contract.der_id == der_id
            assert contract.id == contract_id
        else:
            assert contract is None

    @pytest.mark.parametrize(
        "eager_load",
        [True, False],
    )
    def test_get_contracts_by_id(self, db_session, contract_setup, eager_load):
        der_id = contract_setup.der_id
        with db_session() as session:
            contracts = ContractRepository(session).get_unexpired_contracts_by_der_id(
                der_id, eager_load
            )
        assert len(contracts) == 1
        assert contracts[0].der_id == der_id

    @pytest.mark.parametrize(
        "value",
        ["RandomDERID", None, ""],
    )
    def test_get_contracts_by_id_invalid_der(self, db_session, value):
        with db_session() as session:
            contracts = ContractRepository(session).get_unexpired_contracts_by_der_id(value)
        assert len(contracts) == 0

    def test_get_contracts_by_id_expired_cancelled(
        self, db_session, contract_setup_expired_cancelled
    ):
        der_id = contract_setup_expired_cancelled.der_id
        with db_session() as session:
            contracts = ContractRepository(session).get_unexpired_contracts_by_der_id(der_id, True)
        assert len(contracts) == 0

    def test_get_contracts_by_service_provider_id(self, db_session, contract_setup):
        with db_session() as session:
            contracts = ContractRepository(session).get_contracts_by_service_provider_id(1)
        assert len(contracts) == 1
