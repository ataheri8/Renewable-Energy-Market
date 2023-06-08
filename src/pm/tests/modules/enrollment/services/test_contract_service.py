import pendulum
import pytest
from testfixtures import LogCapture

from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.modules.enrollment.services.contract import (
    ContractService,
    CreateUpdateContractDict,
    InvalidContractArgs,
    InvalidUndoCancellation,
)
from pm.modules.enrollment.services.enrollment import EnrollmentService
from pm.modules.progmgmt.enums import ProgramStatus
from pm.modules.progmgmt.models.program import Program
from pm.tests import factories
from shared.enums import ProgramTypeEnum


class TestContractService:
    def test_validate_required_fields_contract(self):
        data = dict(
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
        ContractService()._validate_required_fields_contract(data)

    @pytest.mark.parametrize(
        "contract_args",
        [
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    program_id=1,
                ),
                id="not-all-fields-1-1",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                ),
                id="not-all-fields-1-2",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    service_provider_id=1,
                ),
                id="not-all-fields-1-3",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                ),
                id="not-all-fields-1-4",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                ),
                id="not-all-fields-1-5",
            ),
            pytest.param(
                dict(
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                ),
                id="not-all-fields-1-6",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    ),
                ),
                id="not-all-fields-2",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    ),
                ),
                id="not-all-fields-3",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    ),
                ),
                id="not-all-fields-4",
            ),
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                    ),
                ),
                id="not-all-fields-5",
            ),
        ],
    )
    def test_validate_contract_creation_data_error(self, contract_args):
        with pytest.raises(InvalidContractArgs):
            ContractService().validate_contract_creation_data(contract_args)

    def test__validate_required_fields_contract(self):
        data = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        ContractService()._validate_required_fields_contract(data)

    def test__validate_required_fields_contract_fail(self):
        data = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        with pytest.raises(InvalidContractArgs):
            ContractService()._validate_required_fields_contract(data)

    def test__validate_dynamic_operating_envelopes_for_doe_contract(self):
        contract_args = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        ContractService()._validate_dynamic_operating_envelopes_for_doe_contract(contract_args)

    @pytest.mark.parametrize(
        "contract_args",
        [
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    )
                ),
                id="doe-1-1",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=-10.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    )
                ),
                id="doe-1-2",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    )
                ),
                id="doe-2-1",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=-10.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    )
                ),
                id="doe-2-2",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_export_kw=0.0,
                    )
                ),
                id="doe-3-1",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=-10.0,
                        default_limits_reactive_power_export_kw=0.0,
                    )
                ),
                id="doe-3-2",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                    )
                ),
                id="doe-4-1",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=0.0,
                        default_limits_active_power_export_kw=0.0,
                        default_limits_reactive_power_import_kw=0.0,
                        default_limits_reactive_power_export_kw=-10.0,
                    )
                ),
                id="doe-4-2",
            ),
            pytest.param(
                dict(
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=None,
                        default_limits_active_power_export_kw=10.0,
                        default_limits_reactive_power_import_kw=10.0,
                        default_limits_reactive_power_export_kw=1.0,
                    )
                ),
                id="doe-5-1",
            ),
        ],
    )
    def test__validate_dynamic_operating_envelopes_for_doe_contract_fail(self, contract_args):
        contract_args = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
            **contract_args,
        )
        with pytest.raises(InvalidContractArgs):
            ContractService()._validate_dynamic_operating_envelopes_for_doe_contract(contract_args)

    @pytest.mark.parametrize(
        "contract_args",
        [
            pytest.param(
                dict(
                    contract_status=ContractStatus.ACCEPTED,
                    contract_type=ContractType.ENROLLMENT_CONTRACT,
                    enrollment_request_id=1,
                    program_id=1,
                    der_id="test_der_id",
                    service_provider_id=1,
                ),
                id="all-fields",
            ),
        ],
    )
    def test_create_contract(self, contract_args):
        with LogCapture() as logs:
            contract = ContractService().create_contract(**contract_args)
        assert contract.contract_status == contract_args["contract_status"]
        assert contract.contract_type == contract_args["contract_type"]
        assert "Created Contract" in str(logs)

    @pytest.mark.parametrize(
        "is_active",
        [
            pytest.param(False, id="not_active"),
            pytest.param(True, id="active"),
        ],
    )
    def test_create_contract_from_enrollment_request(self, is_active):
        args = dict(
            program_id=1,
            service_provider_id="test service id",
            der_id="test der id",
        )
        enrollment = EnrollmentService().create_enrollment_request(**args)
        program = Program.factory("name", ProgramTypeEnum.GENERIC)

        if is_active:
            program._set_start_end_time(
                start=pendulum.now().subtract(months=1),
                end=pendulum.now().add(months=1),
            )
            program.status = ProgramStatus.ACTIVE
        else:
            program.status = ProgramStatus.PUBLISHED
        with LogCapture() as logs:
            contract = ContractService().create_contract_from_enrollment_request(
                enrollment, program
            )
        assert contract is not None
        assert contract.contract_type == ContractType.ENROLLMENT_CONTRACT
        assert "Created Contract" in str(logs)
        if is_active:
            assert contract.contract_status == ContractStatus.ACTIVE
        else:
            assert contract.contract_status == ContractStatus.ACCEPTED

    def test_create_contract_from_enrollment_request_no_program_status(self):
        args = dict(
            program_id=1,
            service_provider_id="test service id",
            der_id="test der id",
        )
        enrollment = EnrollmentService().create_enrollment_request(**args)
        program = Program.factory("name", ProgramTypeEnum.GENERIC)
        program.status = None
        with pytest.raises(InvalidContractArgs) as excep:
            ContractService().create_contract_from_enrollment_request(enrollment, program)
        assert excep.value.message == (
            "Contract Create failed due to: Cannot determine "
            + "the contract status from the program status"
        )

    def test_set_contract_fields(self):
        # Create a new Contract

        create_args = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)

        # Update the Contract

        args: CreateUpdateContractDict = dict(
            **create_args,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        with LogCapture() as logs:
            contract = ContractService().set_contract_fields(contract, args)
        assert contract.dynamic_operating_envelopes["default_limits_active_power_import_kw"] >= 0
        assert "Saved Contract" in str(logs)

    def test__update_contract_fields(self):
        # Create a new Contract

        create_args = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)

        # Update the Contract with doe values

        args: CreateUpdateContractDict = dict(
            **create_args,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        contract = ContractService()._update_contract_fields(contract, args)
        assert contract.dynamic_operating_envelopes["default_limits_active_power_import_kw"] >= 0
        assert contract.dynamic_operating_envelopes["default_limits_active_power_export_kw"] >= 0
        assert contract.dynamic_operating_envelopes["default_limits_reactive_power_import_kw"] >= 0
        assert contract.dynamic_operating_envelopes["default_limits_reactive_power_export_kw"] >= 0

        # Update the Contract with demand mgmt values

        args: CreateUpdateContractDict = dict(
            **create_args,
            demand_response=dict(import_target_capacity=0.0, export_target_capacity=0.0),
        )
        contract = ContractService()._update_contract_fields(contract, args)
        assert contract.demand_response["import_target_capacity"] >= 0
        assert contract.demand_response["export_target_capacity"] >= 0

    def test__update_contract_fields_return_invalid_args(self):
        # Create a new Contract

        create_args = dict(
            contract_status=ContractStatus.EXPIRED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)

        # Update the Contract with doe values

        args: CreateUpdateContractDict = dict(
            **create_args,
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=0.0,
                default_limits_active_power_export_kw=0.0,
                default_limits_reactive_power_import_kw=0.0,
                default_limits_reactive_power_export_kw=0.0,
            ),
        )
        with pytest.raises(InvalidContractArgs):
            ContractService()._update_contract_fields(contract, args)

    def test__update_contract_status(self):
        # Create a new Contract

        create_args = dict(
            contract_status=ContractStatus.ACCEPTED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)
        assert contract.contract_status == ContractStatus.ACCEPTED
        # Update the Contract's status

        with LogCapture() as logs:
            contract = ContractService().update_contract_status(
                contract, contract_status=ContractStatus.USER_CANCELLED
            )
        assert contract.contract_status != ContractStatus.ACCEPTED
        assert "Updated Contract Status" in str(logs)

    @pytest.mark.parametrize(
        "contract_status,can_undo_cancel",
        [
            pytest.param(ContractStatus.ACCEPTED, False, id="ACCEPTED"),
            pytest.param(ContractStatus.ACTIVE, False, id="ACTIVE"),
            pytest.param(ContractStatus.EXPIRED, False, id="EXPIRED"),
            pytest.param(ContractStatus.USER_CANCELLED, True, id="USER CANCELLED"),
        ],
    )
    def test_check_undo_cancel_contract_request(self, db_session, contract_status, can_undo_cancel):
        # Create a new Contract
        program = factories.ProgramFactory(id=1)
        create_args = dict(
            contract_status=contract_status,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)
        assert contract.contract_status == contract_status
        if not can_undo_cancel:
            with pytest.raises(InvalidUndoCancellation) as excep:
                ContractService().check_undo_cancel_contract_request(contract, program)
            assert excep.value.message == (
                "The contract cannot be re-activated as "
                + "previously it has not been cancelled by user"
            )
        else:
            assert ContractService().check_undo_cancel_contract_request(contract, program) is None

    def test_find_status_after_undo_cancellation(self, db_session):
        # Create a new Contract
        program = factories.ProgramFactory(id=1)
        create_args = dict(
            contract_status=ContractStatus.USER_CANCELLED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)
        assert contract.contract_status == ContractStatus.USER_CANCELLED
        post_undo_cancellation_status = ContractService().find_status_after_undo_cancellation(
            program
        )
        assert post_undo_cancellation_status == ContractStatus.ACCEPTED

    def test_find_active_status_after_undo_cancellation(self, db_session):
        # Create a new Contract
        program = factories.SharedFieldsProgramFactory(
            id=1,
            start_date=pendulum.now().subtract(months=1),
            dispatch_notifications=[],
            status=ProgramStatus.ACTIVE,
        )
        create_args = dict(
            contract_status=ContractStatus.USER_CANCELLED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)
        assert contract.contract_status == ContractStatus.USER_CANCELLED
        post_undo_cancellation_status = ContractService().find_status_after_undo_cancellation(
            program
        )
        assert post_undo_cancellation_status == ContractStatus.ACTIVE

    @pytest.mark.parametrize(
        "contract_status,can_cancel",
        [
            pytest.param(ContractStatus.ACCEPTED, True, id="ACCEPTED"),
            pytest.param(ContractStatus.ACTIVE, True, id="ACTIVE"),
            pytest.param(ContractStatus.USER_CANCELLED, False, id="USER CANCELLED"),
            pytest.param(ContractStatus.EXPIRED, False, id="EXPIRED"),
        ],
    )
    def test_check_cancel_contract_request(self, contract_status, can_cancel):
        # Create a new Contract

        create_args = dict(
            contract_status=contract_status,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)
        assert contract.contract_status == contract_status
        cancellation_possible = ContractService().check_cancel_contract_request(contract)
        assert cancellation_possible == can_cancel

    @pytest.mark.parametrize(
        "contract_status,can_update",
        [
            pytest.param(ContractStatus.ACCEPTED, True, id="ACCEPTED"),
            pytest.param(ContractStatus.ACTIVE, True, id="ACTIVE"),
            pytest.param(ContractStatus.USER_CANCELLED, False, id="USER CANCELLED"),
            pytest.param(ContractStatus.EXPIRED, False, id="EXPIRED"),
        ],
    )
    def test_can_contract_be_updated(self, contract_status, can_update):
        # Create a new Contract

        create_args = dict(
            contract_status=contract_status,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        contract = ContractService().create_contract(**create_args)
        assert contract.contract_status == contract_status
        cancellation_possible = ContractService()._can_contract_be_updated(contract)
        assert cancellation_possible == can_update

    @pytest.mark.parametrize(
        "program_status,contract_status",
        [
            pytest.param(ProgramStatus.DRAFT, ContractStatus.ACCEPTED, id="DRAFT"),
            pytest.param(ProgramStatus.ACTIVE, ContractStatus.ACTIVE, id="ACTIVE"),
            pytest.param(ProgramStatus.PUBLISHED, ContractStatus.ACCEPTED, id="PUBLISHED"),
            pytest.param(ProgramStatus.ARCHIVED, ContractStatus.EXPIRED, id="ARCHIVED"),
            pytest.param(None, None),
        ],
    )
    def test__map_program_status_to_contract_status(self, program_status, contract_status):
        contract_status_from_program = ContractStatus.map_program_status_to_contract_status(
            program_status
        )
        assert contract_status_from_program == contract_status
