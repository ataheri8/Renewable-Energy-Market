import uuid
from datetime import datetime, timezone

import pendulum
import pytest
from werkzeug.datastructures import FileStorage

from pm.modules.enrollment.enums import (
    ContractStatus,
    ContractType,
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.modules.enrollment.models.enrollment import (
    DemandResponseDict,
    DynamicOperatingEnvelopesDict,
    EnrollmentRequest,
)
from pm.modules.enrollment.services.contract import ContractService
from pm.modules.enrollment.services.enrollment import (
    CreateUpdateEnrollmentRequestDict,
    EnrollmentRequestGenericFieldsDict,
    EnrollmentRequestNotAllowed,
    EnrollmentService,
    InvalidEnrollmentRequestArgs,
)
from pm.modules.progmgmt.models import Program
from pm.tests_acceptance.mixins import TestDataMixin
from shared.enums import ProgramTypeEnum
from shared.exceptions import LoggedError
from shared.tools.utils import validate_uploaded_csv_and_row_count


class TestEnrollmentService(TestDataMixin):
    def test_create_enrollment(self):
        args = dict(
            program_id=1,
            service_provider_id="test service id",
            der_id="test der id",
        )
        enrollment = EnrollmentService().create_enrollment_request(**args)
        assert enrollment

    def test_reject_enrollment(self):
        enrollment = EnrollmentRequest(enrollment_status=EnrollmentRequestStatus.ACCEPTED)
        EnrollmentService().reject_enrollment_request(
            enrollment, EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA
        )
        assert enrollment.enrollment_status == EnrollmentRequestStatus.REJECTED

    def test_accept_enrollment(self):
        enrollment = EnrollmentRequest()
        EnrollmentService().accept_enrollment_request(enrollment)
        assert enrollment.enrollment_status == EnrollmentRequestStatus.ACCEPTED

    def test_set_enrollment_request_fields_general(self):
        enrollment = EnrollmentRequest()
        program = Program()
        data = CreateUpdateEnrollmentRequestDict(
            general_fields=EnrollmentRequestGenericFieldsDict(
                program_id=5,
                service_provider_id=3,
                der_id="fake",
                enrollment_status=EnrollmentRequestStatus.REJECTED,
                rejection_reason=EnrollmentRejectionReason.DER_NOT_FOUND,
            )
        )
        enrollment = EnrollmentService().set_enrollment_request_fields(enrollment, data, program)
        assert enrollment.program_id == 5
        assert enrollment.service_provider_id == 3
        assert enrollment.der_id == "fake"
        assert enrollment.enrollment_status == EnrollmentRequestStatus.REJECTED
        assert enrollment.rejection_reason == EnrollmentRejectionReason.DER_NOT_FOUND

    @pytest.mark.parametrize(
        "program_type,define_contractual_target_capacity",
        [
            pytest.param(ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES, False),
            pytest.param(ProgramTypeEnum.DEMAND_MANAGEMENT, True),
            pytest.param(ProgramTypeEnum.DEMAND_MANAGEMENT, False),
            pytest.param(ProgramTypeEnum.GENERIC, True),
            pytest.param(ProgramTypeEnum.GENERIC, False),
        ],
    )
    def test_set_enrollment_request_fields_program_specific(
        self, program_type, define_contractual_target_capacity
    ):
        enrollment = EnrollmentRequest()
        program = Program(
            program_type=program_type,
            define_contractual_target_capacity=define_contractual_target_capacity,
        )
        data = CreateUpdateEnrollmentRequestDict(
            general_fields=EnrollmentRequestGenericFieldsDict(
                program_id=5,
                service_provider_id=3,
                der_id="fake",
                enrollment_status=EnrollmentRequestStatus.REJECTED,
                rejection_reason=EnrollmentRejectionReason.DER_NOT_FOUND,
            ),
            dynamic_operating_envelopes=DynamicOperatingEnvelopesDict(
                default_limits_active_power_import_kw=234.1,
                default_limits_active_power_export_kw=234.2,
                default_limits_reactive_power_import_kw=234.3,
                default_limits_reactive_power_export_kw=234.4,
            ),
            demand_response=DemandResponseDict(
                import_target_capacity=123.4, export_target_capacity=123.5
            ),
        )
        enrollment = EnrollmentService().set_enrollment_request_fields(enrollment, data, program)
        if program_type == ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES:
            assert enrollment.dynamic_operating_envelopes == data["dynamic_operating_envelopes"]
            assert enrollment.demand_response != data["demand_response"]
        elif define_contractual_target_capacity:
            assert enrollment.dynamic_operating_envelopes != data["dynamic_operating_envelopes"]
            assert enrollment.demand_response == data["demand_response"]

    @pytest.mark.parametrize(
        "program_type,define_contractual_target_capacity",
        [
            pytest.param(ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES, False),
            pytest.param(ProgramTypeEnum.DEMAND_MANAGEMENT, True),
            pytest.param(ProgramTypeEnum.DEMAND_MANAGEMENT, False),
            pytest.param(ProgramTypeEnum.GENERIC, True),
            pytest.param(ProgramTypeEnum.GENERIC, False),
        ],
    )
    def test_set_enrollment_request_fields_program_specific_not_update(
        self, program_type, define_contractual_target_capacity
    ):
        enrollment = EnrollmentRequest()
        program = Program(
            program_type=program_type,
            define_contractual_target_capacity=define_contractual_target_capacity,
        )

        data = {}
        enrollment = EnrollmentService().set_enrollment_request_fields(enrollment, data, program)
        assert enrollment.program_id is None
        assert enrollment.service_provider_id is None
        assert enrollment.der_id is None

        data = CreateUpdateEnrollmentRequestDict(
            general_fields=EnrollmentRequestGenericFieldsDict(
                program_id=5,
                service_provider_id=3,
                der_id="fake",
                enrollment_status=EnrollmentRequestStatus.REJECTED,
                rejection_reason=EnrollmentRejectionReason.DER_NOT_FOUND,
            )
        )
        enrollment = EnrollmentService().set_enrollment_request_fields(enrollment, data, program)
        assert enrollment.dynamic_operating_envelopes is None
        assert enrollment.demand_response is None

    def test_create_enrollment_request_fields_program_specific_failed_doe_params(self):
        program = Program(program_type=ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES)
        data = CreateUpdateEnrollmentRequestDict(
            general_fields=EnrollmentRequestGenericFieldsDict(
                program_id=1, service_provider_id=1, der_id="fake"
            )
        )
        with pytest.raises(InvalidEnrollmentRequestArgs) as excep:
            EnrollmentService().validate_enrollment_request(data, program)
        assert excep.value.message == (
            "Enrollment Request program type is "
            "DYNAMIC OPERATING ENVELOPES but it is missing default limits"
        )

    def test_create_enrollment_request_fields_program_specific_failed_non_int_sp_id(self):
        program = Program(program_type=ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES)
        data = CreateUpdateEnrollmentRequestDict(
            general_fields=EnrollmentRequestGenericFieldsDict(
                program_id=1, service_provider_id="Fake", der_id="fake"
            )
        )
        with pytest.raises(InvalidEnrollmentRequestArgs) as excep:
            EnrollmentService().validate_enrollment_request(data, program)
        assert excep.value.message == ("Service provider id should be an integer")

    def test_validate_enrollment_request_csv_no_file(self):
        with pytest.raises(LoggedError) as excep:
            validate_uploaded_csv_and_row_count(file=None)
        assert "Missing File" == str(excep.value)

    def test_validate_enrollment_request_invalid_csv(self):
        filename = "invalid_file_type.json"
        filepath = self._get_test_data_path(filename)
        with pytest.raises(LoggedError) as excep:
            with open(filepath, "rb") as f:
                f_obj = FileStorage(f, filename)
                validate_uploaded_csv_and_row_count(file=f_obj)
        assert "Invalid file extension. Only CSV allowed" == str(excep.value)

    @pytest.mark.parametrize(
        "program_name,service_provider_id_1,der_id_1,rejection_reason,rejection_text",
        [
            pytest.param(
                "Program Name One",
                1,
                str(uuid.uuid4()),
                EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA,
                "DER does not meet the program criteria",
            ),
            pytest.param(
                "Second Program Name!!!",
                123456789,
                "My Favourite DER ID",
                EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND,
                "DER eligibility data not found in the DER Warehouse",
            ),
        ],
    )
    def test_create_enrollment_report(
        self,
        program_name,
        service_provider_id_1,
        der_id_1,
        rejection_reason,
        rejection_text,
    ):
        expected = (
            "Program Name,DER ID,Service Provider ID,Enrollment Time,Enrollment User "
            "ID,Enrollment Status,Rejection Reason\r\n"
            f"{program_name},{der_id_1},{service_provider_id_1},"
            f"2022-11-09T00:00:00+00:00,,REJECTED,{rejection_text}\r\n"
            f"{program_name},der_2,1,2022-11-08T00:00:00+00:00,,ACCEPTED,\r\n"
        )
        program_1 = Program(id=1, name=program_name)

        enrollment_1 = EnrollmentRequest(
            id=1,
            program=program_1,
            service_provider_id=service_provider_id_1,
            der_id=der_id_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            rejection_reason=rejection_reason,
            created_at=datetime(2022, 11, 9, tzinfo=timezone.utc),
        )
        enrollment_2 = EnrollmentRequest(
            id=2,
            program=program_1,
            service_provider_id=1,
            der_id="der_2",
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            created_at=datetime(2022, 11, 8, tzinfo=timezone.utc),
        )

        file = EnrollmentService().create_enrollment_report([enrollment_1, enrollment_2])
        text = file.read().decode(encoding="utf-8")
        assert text == expected

    def test_create_enrollment_report_empty(self):
        expected = (
            "Program Name,DER ID,Service Provider ID,Enrollment Time,Enrollment User "
            "ID,Enrollment Status,Rejection Reason\r\n"
        )

        file = EnrollmentService().create_enrollment_report([])
        text = file.read().decode(encoding="utf-8")
        assert text == expected

    def test_create_enrollment_allowed_check_program_end_date(self):
        create_args = dict(
            contract_status=ContractStatus.SYSTEM_CANCELLED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        existing_contract = ContractService().create_contract(**create_args)

        program = Program(
            start_date=pendulum.now().subtract(hours=2),
            end_date=pendulum.now().add(hours=1),
        )
        try:
            EnrollmentService().create_enrollment_allowed(program, existing_contract)
        except EnrollmentRequestNotAllowed:
            assert (  # noqa: B011
                False
            ), "EnrollmentService.create_enrollment_allowed() raised a false exception"

        program = Program(
            start_date=pendulum.now().subtract(hours=2),
            end_date=pendulum.now().subtract(hours=1),
        )
        with pytest.raises(EnrollmentRequestNotAllowed) as excep:
            EnrollmentService().create_enrollment_allowed(program, existing_contract)

        assert excep.value.message == "Enrollment Request is for program that has ended"

    @pytest.mark.parametrize(
        "contract_status",
        [
            pytest.param(ContractStatus.ACCEPTED, id="ACCEPTED"),
            pytest.param(ContractStatus.ACTIVE, id="ACTIVE"),
            pytest.param(ContractStatus.USER_CANCELLED, id="USER_CANCELLED"),
            pytest.param(ContractStatus.EXPIRED, id="EXPIRED"),
        ],
    )
    def test_create_enrollment_allowed_check_existing_contracts(self, contract_status):
        create_args = dict(
            contract_status=ContractStatus.SYSTEM_CANCELLED,
            contract_type=ContractType.ENROLLMENT_CONTRACT,
            enrollment_request_id=1,
            program_id=1,
            der_id="test_der_id",
            service_provider_id=1,
        )
        existing_contract = ContractService().create_contract(**create_args)

        program = Program(
            start_date=pendulum.now().subtract(hours=2),
            end_date=pendulum.now().add(hours=1),
        )
        existing_contract = ContractService().update_contract_status(
            existing_contract, contract_status
        )
        with pytest.raises(EnrollmentRequestNotAllowed) as excep:
            EnrollmentService().create_enrollment_allowed(program, existing_contract)

        assert (
            excep.value.message
            == "Contract already exists for this program, service provider, and der"
        )
