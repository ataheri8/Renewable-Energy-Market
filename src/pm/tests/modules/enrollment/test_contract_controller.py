import pytest

from pm.modules.enrollment.contract_controller import ContractController
from pm.modules.enrollment.contract_repository import ContractNotFound
from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.modules.enrollment.models.enrollment import Contract
from pm.modules.enrollment.services.contract import (
    CreateUpdateContractDict,
    InvalidProgramStatusForContract,
    InvalidUndoCancellation,
)
from pm.modules.outbox.model import Outbox
from pm.modules.progmgmt.enums import ProgramStatus
from pm.tests import factories


class TestContractController:
    def _get_all_contract(self, db_session) -> list[Contract]:
        with db_session() as session:
            return session.query(Contract).all()

    def _get_all_outbox(self, db_session) -> list[Outbox]:
        with db_session() as session:
            return session.query(Outbox).all()

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
        contract = factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
        )
        return {"der": der1, "contract": contract}

    @pytest.mark.parametrize(
        "contract_args,status",
        [
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    ),
                ),
                "CREATED",
                id="all-fields",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    der_id="test_der_id",
                    program_id=1,
                    service_provider_id=1,
                ),
                "NOT_CREATED",
                id="missing-fields-1-1",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    service_provider_id=1,
                ),
                "NOT_CREATED",
                id="missing-fields-1-2",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                ),
                "NOT_CREATED",
                id="missing-fields-1-3",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                ),
                "NOT_CREATED",
                id="missing-fields-1-4",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                    service_provider_id=1,
                ),
                "NOT_CREATED",
                id="missing-fields-1-5",
            ),
            pytest.param(
                dict(
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                    service_provider_id=1,
                ),
                "NOT_CREATED",
                id="missing-fields-1-6",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    ),
                ),
                "NOT_CREATED",
                id="missing-fields-4",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=-10.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    ),
                ),
                "NOT_CREATED",
                id="missing-fields-5",
            ),
        ],
    )
    def test_create_contract(self, db_session, contract_args, status):
        # Create an enrollment in the db for the contract
        enrollment_request_id = 1
        der = factories.DerFactory(der_id="test_der_id")
        factories.EnrollmentRequestFactory(id=enrollment_request_id, der=der)
        service_provider_id = 1
        factories.ServiceProviderFactory(id=service_provider_id)
        ids = ContractController().create_contract([contract_args])
        assert ids[0]["status"] == status

        contracts = self._get_all_contract(db_session)
        outbox = self._get_all_outbox(db_session)
        if status == "CREATED":
            assert len(contracts) == 1
            assert contracts[0].id == 1
            assert ids[0]["id"] == 1
            assert len(outbox) == 1
            assert outbox[0].id == 1
        else:
            assert len(contracts) == 0
            assert len(outbox) == 0

    def test_update_contract(self, db_session):
        factories.ContractFactory(id=1)
        contract = self._get_all_contract(db_session)[0]

        # Update the Contract with doe values

        args: CreateUpdateContractDict = dict(
            contract_status=contract.contract_status,
            contract_type=contract.contract_type,
            enrollment_request_id=contract.enrollment_request_id,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        ContractController().update_contract(contract.id, args)

        contract = self._get_all_contract(db_session)[0]
        assert contract.dynamic_operating_envelopes["default_limits_active_power_import_kw"] >= 0
        assert contract.dynamic_operating_envelopes["default_limits_active_power_export_kw"] >= 0
        assert contract.dynamic_operating_envelopes["default_limits_reactive_power_import_kw"] >= 0
        assert contract.dynamic_operating_envelopes["default_limits_reactive_power_export_kw"] >= 0

        # Update the Contract with demand mgmt values

        args: CreateUpdateContractDict = dict(
            contract_status=contract.contract_status,
            contract_type=contract.contract_type,
            enrollment_request_id=contract.enrollment_request_id,
            demand_response=dict(import_target_capacity=0.0, export_target_capacity=0.0),
        )
        ContractController().update_contract(contract.id, args)

        contract = self._get_all_contract(db_session)[0]
        assert contract.demand_response["import_target_capacity"] >= 0
        assert contract.demand_response["export_target_capacity"] >= 0

    def test_non_exist_update_contract(self, db_session):
        # Update the Contract with doe values

        args: CreateUpdateContractDict = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        with pytest.raises(ContractNotFound):
            ContractController().update_contract(1, args)

        # Update the Contract with demand mgmt values

        args: CreateUpdateContractDict = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            der_id="test_der_id",
            program_id=1,
            service_provider_id=1,
            demand_response=dict(import_target_capacity=0.0, export_target_capacity=0.0),
        )
        with pytest.raises(ContractNotFound):
            ContractController().update_contract(1, args)

    @pytest.mark.parametrize(
        "contract_status,can_cancelled",
        [
            pytest.param(ContractStatus.ACCEPTED, True, id="ACCEPTED"),
            pytest.param(ContractStatus.ACTIVE, True, id="ACTIVE"),
            pytest.param(ContractStatus.USER_CANCELLED, False, id="USER CANCELLED"),
            pytest.param(ContractStatus.EXPIRED, False, id="EXPIRED"),
        ],
    )
    def test_cancel_contract(self, db_session, contract_status, can_cancelled):
        contract_id = 1
        factories.ContractFactory(id=contract_id, contract_status=contract_status)
        cancelled = ContractController().cancel_contract(contract_id)
        assert cancelled == can_cancelled

    def test_non_exist_cancel_contract(self, db_session):
        with pytest.raises(ContractNotFound):
            ContractController().cancel_contract(1)

    @pytest.mark.parametrize(
        "contract_status,can_undo_cancel",
        [
            pytest.param(ContractStatus.ACCEPTED, False, id="ACCEPTED"),
            pytest.param(ContractStatus.ACTIVE, False, id="ACTIVE"),
            pytest.param(ContractStatus.EXPIRED, False, id="EXPIRED"),
            pytest.param(ContractStatus.USER_CANCELLED, True, id="USER CANCELLED"),
        ],
    )
    def test_undo_cancel_contract(self, db_session, contract_status, can_undo_cancel):
        contract_id = 1
        factories.ContractFactory(id=contract_id, contract_status=contract_status)
        if not can_undo_cancel:
            with pytest.raises(InvalidUndoCancellation) as excep:
                ContractController().undo_cancel_contract(contract_id)
            assert excep.value.message == (
                "The contract cannot be re-activated as "
                + "previously it has not been cancelled by user"
            )
        else:
            assert ContractController().undo_cancel_contract(contract_id) is None

    def test_non_exist_undo_cancel_contract(self, db_session):
        with pytest.raises(ContractNotFound):
            ContractController().undo_cancel_contract(1)

    def test_archived_program_undo_cancel_contract(self, db_session):
        program = factories.ProgramFactory(id=1, status=ProgramStatus.ARCHIVED)
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der1,
        )
        contract = factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
            contract_status=ContractStatus.USER_CANCELLED,
        )
        contract_id = contract.id
        assert contract.contract_status == ContractStatus.USER_CANCELLED
        with pytest.raises(InvalidProgramStatusForContract) as excep:
            ContractController().undo_cancel_contract(contract_id)
        assert excep.value.message == "Cannot re-activate the contract as the program has expired"
        contract = ContractController().get_contract(contract_id, eager_load=True)
        assert contract.contract_status == ContractStatus.USER_CANCELLED

    def test_get_all_contracts(self, db_session):
        num_of_contract = 5
        for _ in range(num_of_contract):
            factories.ContractFactory()
        contracts = ContractController().get_all_contracts()
        assert len(contracts) == num_of_contract

    @pytest.mark.parametrize(
        "contract_exist",
        [
            pytest.param(True, id="one-contract"),
            pytest.param(False, id="zero-contract"),
        ],
    )
    def test_get_contract(self, db_session, contract_exist):
        contract_id = 0
        if contract_exist:
            factories.ContractFactory()
            contract_id = self._get_all_contract(db_session)[0].id
            contract = ContractController().get_contract(contract_id)
            assert contract.id == contract_id
        else:
            with pytest.raises(ContractNotFound):
                ContractController().get_contract(1)

    def test_cancel_contract_by_der_id(self, db_session, contract_setup):
        der_id = contract_setup["der"].der_id
        contract_id = contract_setup["contract"].id
        ContractController().cancel_contracts_by_der_id(str(der_id))
        contract = ContractController().get_contract(contract_id, eager_load=True)
        assert contract.contract_status == ContractStatus.SYSTEM_CANCELLED
        der_obj = contract.der
        assert der_obj.der_id == der_id

    def test_cancel_contract_by_der_id_invalid_der(self, db_session, contract_setup):
        contract_id = contract_setup["contract"].id
        ContractController().cancel_contracts_by_der_id(str("RandomDERID"))
        contract = ContractController().get_contract(contract_id, eager_load=True)
        assert contract.contract_status != ContractStatus.SYSTEM_CANCELLED

    def test_activate_contracts(self, db_session):
        program = factories.ProgramFactory(id=1, status=ProgramStatus.ACTIVE)
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der1,
        )
        contract = factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
        )
        contract_id = contract.id
        assert contract.contract_status == ContractStatus.ACCEPTED
        ContractController().activate_contracts()
        contract = ContractController().get_contract(contract_id, eager_load=True)
        assert contract.contract_status == ContractStatus.ACTIVE

    def test_expire_contracts_archived_programs(self, db_session):
        program = factories.ProgramFactory(id=1, status=ProgramStatus.ARCHIVED)
        service_provider_1 = factories.ServiceProviderFactory(id=1)
        der1 = factories.DerFactory(der_id="der_1", service_provider_id=service_provider_1.id)
        der2 = factories.DerFactory(der_id="der_2", service_provider_id=service_provider_1.id)
        enrollment_request_1 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der1,
        )
        enrollment_request_2 = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider_1,
            der=der2,
        )
        contract_1 = factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_1,
            der=der1,
            contract_status=ContractStatus.ACCEPTED,
        )
        contract_2 = factories.ContractFactory(
            id=2,
            program=program,
            service_provider=service_provider_1,
            enrollment_request=enrollment_request_2,
            der=der2,
            contract_status=ContractStatus.ACTIVE,
        )
        contract_1_id = contract_1.id
        contract_2_id = contract_2.id
        assert contract_1.contract_status == ContractStatus.ACCEPTED
        assert contract_2.contract_status == ContractStatus.ACTIVE
        ContractController().expire_contracts_archived_programs()
        contract_1 = ContractController().get_contract(contract_1_id, eager_load=True)
        contract_2 = ContractController().get_contract(contract_2_id, eager_load=True)
        assert contract_1.contract_status == ContractStatus.EXPIRED
        assert contract_2.contract_status == ContractStatus.EXPIRED
