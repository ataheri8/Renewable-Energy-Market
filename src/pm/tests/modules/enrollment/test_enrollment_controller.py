from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from testfixtures import LogCapture
from werkzeug.datastructures import FileStorage

from pm.modules.derinfo.enums import LimitUnitType
from pm.modules.enrollment.controller import EnrollmentController
from pm.modules.enrollment.enums import EnrollmentCRUDStatus, EnrollmentRequestStatus
from pm.modules.enrollment.models.enrollment import Contract, EnrollmentRequest
from pm.modules.progmgmt.enums import ProgramStatus
from pm.modules.progmgmt.models.program import ResourceEligibilityCriteria
from pm.modules.progmgmt.repository import ProgramNotFound
from pm.modules.serviceprovider.controller import ServiceProviderController
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin
from shared.enums import ProgramTypeEnum


@pytest.fixture
def enrollment():
    return factories.EnrollmentRequestFactory(
        der_id="test der id",
        enrollment_status=EnrollmentRequestStatus.ACCEPTED,
        dynamic_operating_envelopes=dict(
            default_limits_active_power_import_kw=50,
            default_limits_active_power_export_kw=50,
            default_limits_reactive_power_import_kw=50,
            default_limits_reactive_power_export_kw=50,
        ),
        demand_response=dict(
            import_target_capacity=300.01,
            export_target_capacity=30.01,
        ),
    )


@pytest.fixture
def enrollment_dict():
    return dict(
        general_fields=dict(
            program_id=1,
            service_provider_id=1,
            der_id="test_der_id",
        ),
        dynamic_operating_envelopes=dict(
            default_limits_active_power_import_kw=50,
            default_limits_active_power_export_kw=50,
            default_limits_reactive_power_import_kw=50,
            default_limits_reactive_power_export_kw=50,
        ),
        demand_response=dict(
            import_target_capacity=300.01,
            export_target_capacity=30.01,
        ),
    )


class TestEnrollmentController(TestDataMixin):
    def _get_all_enrollments(self, db_session) -> list[EnrollmentRequest]:
        with db_session() as session:
            return session.query(EnrollmentRequest).all()

    def _get_all_contracts(self, db_session) -> list[Contract]:
        with db_session() as session:
            return session.query(Contract).all()

    @pytest.mark.parametrize(
        "enrollment_args",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                    demand_response=dict(
                        import_target_capacity=300.01,
                        export_target_capacity=30.01,
                    ),
                ),
                id="all-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    demand_response=dict(
                        import_target_capacity=300.01,
                        export_target_capacity=30.01,
                    ),
                ),
                id="minimum-fields",
            ),
        ],
    )
    def test_create_enrollment(self, enrollment_args, db_session):
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        factories.DerFactory(der_id="test der id")  # der_id from enrollment args
        EnrollmentController().create_enrollment_requests([enrollment_args])
        enrollments = self._get_all_enrollments(db_session)
        assert len(enrollments) == 1

    def test_create_enrollment_fail_draft_program(self, db_session):
        program_id = 1
        factories.ProgramFactory(
            id=program_id, status=ProgramStatus.DRAFT
        )  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        factories.DerFactory(der_id="test der id")  # der_id from enrollment args
        enrollment_args = dict(
            general_fields=dict(
                program_id=1,
                service_provider_id=1,
                der_id="test der id",
            ),
            dynamic_operating_envelopes=dict(
                default_limits_active_power_import_kw=50,
                default_limits_active_power_export_kw=50,
                default_limits_reactive_power_import_kw=50,
                default_limits_reactive_power_export_kw=50,
            ),
            demand_response=dict(
                import_target_capacity=300.01,
                export_target_capacity=30.01,
            ),
        )

        r = EnrollmentController().create_enrollment_requests([enrollment_args])
        assert r == [
            {
                "id": None,
                "status": EnrollmentCRUDStatus.NOT_CREATED,
                "message": f"program with ID {program_id} is in draft status",
                "data": enrollment_args,
            }
        ]
        enrollments = self._get_all_enrollments(db_session)
        assert len(enrollments) == 0

    @pytest.mark.parametrize(
        "enrollment_args,missing_entity",
        [
            pytest.param(
                dict(
                    general_fields=dict(),
                ),
                "program_id",
                id="no-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        der_id="test der id",
                        enrollment_status=EnrollmentRequestStatus.ACCEPTED,
                    )
                ),
                "service_provider_id",
                id="only-missing-service_provider_id",
            ),
        ],
    )
    def test_create_enrollment_fail_required_general_field_missing(
        self, db_session, enrollment_args, missing_entity
    ):
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        enrollment_req = EnrollmentController().create_enrollment_requests([enrollment_args])
        assert missing_entity.lower() in enrollment_req[0]["message"].lower()
        assert "missing" in enrollment_req[0]["message"].lower()

    # Integration test for bdd scenario PM-671
    @pytest.mark.parametrize(
        "enrollment_args",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    demand_response=dict(
                        import_target_capacity=300.01,
                        export_target_capacity=30.01,
                    ),
                )
            ),
        ],
    )
    def test_enrollment_event_triggered_in_enrollment_create(self, db_session, enrollment_args):
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        factories.DerFactory(der_id="test der id")
        with LogCapture() as logs:
            EnrollmentController().create_enrollment_requests([enrollment_args])
        assert "Created Enrollment Request" in str(logs)

    @pytest.mark.parametrize(
        "enrollment_args,message",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=2,
                        der_id="test der id",
                    )
                ),
                "Service Provider with id 2 is not found",
            ),
        ],
    )
    def test_create_enrollment_failure_service_provider_not_found(
        self, db_session, enrollment_args, message
    ):
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        enrollment_req = EnrollmentController().create_enrollment_requests([enrollment_args])
        assert enrollment_req[0]["status"] == EnrollmentCRUDStatus.NOT_CREATED
        assert message.lower() in enrollment_req[0]["message"].lower()

    @pytest.mark.parametrize(
        "enrollment_args,message",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    )
                ),
                "Service Provider with id 1 is not active",
            ),
        ],
    )
    def test_create_enrollment_failure_service_provider_not_active(
        self, db_session, enrollment_args, message
    ):
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        ServiceProviderController().disable_service_provider(1)
        enrollment_req = EnrollmentController().create_enrollment_requests([enrollment_args])
        assert enrollment_req[0]["status"] == EnrollmentCRUDStatus.NOT_CREATED
        assert message.lower() in enrollment_req[0]["message"].lower()

    @pytest.mark.parametrize(
        "enrollment_args,message",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=2,
                        der_id="test der id",
                    )
                ),
                "Service Provider with id 2 is not found",
            ),
        ],
    )
    def test_create_enrollment_endpoint_failure_service_provider_not_found(
        self, db_session, enrollment_args, message
    ):
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        enrollment_req = EnrollmentController().create_enrollment_requests([enrollment_args])
        assert enrollment_req[0]["status"] == EnrollmentCRUDStatus.NOT_CREATED
        assert message.lower() in enrollment_req[0]["message"].lower()

    @pytest.mark.parametrize(
        "enrollment_args,message,program_type",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                        enrollment_status="ACCEPTED",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Active Power Import (kW) should be provided",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-1a",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                        enrollment_status="ACCEPTED",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=-50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Active Power Import (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-1b",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Active Power Export (kW) should be provided",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-2a",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=-50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Active Power Export (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-2b",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Reactive Power Import (kW) should be provided",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-3a",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=-50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Reactive Power Import (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-3b",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                    ),
                ),
                "Reactive Power Export (kW) should be provided",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-4a",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=-50,
                    ),
                ),
                "Reactive Power Export (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-4b",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=None,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Active Power Import (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-5a",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=None,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Active Power Export (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-5b",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=None,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                "Reactive Power Import (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-5c",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=None,
                    ),
                ),
                "Reactive Power Export (kW) should not be negative",
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                id="dynamic_operating_envelopes_param_incorrect-5d",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                ),
                "Enrollment Request program has define_contractual_target_capacity "
                "set to True but it is missing contractual target capacity",
                ProgramTypeEnum.DEMAND_MANAGEMENT,
                id="demand_response",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                ),
                "Enrollment Request program has define_contractual_target_capacity "
                "set to True but it is missing contractual target capacity",
                ProgramTypeEnum.GENERIC,
                id="generic",
            ),
        ],
    )
    def test_create_enrollment_not_created_error(
        self, db_session, enrollment_args, message, program_type
    ):
        if program_type in (ProgramTypeEnum.GENERIC, ProgramTypeEnum.DEMAND_MANAGEMENT):
            factories.ProgramFactory(
                id=1,
                program_type=program_type,
                define_contractual_target_capacity=True,
            )  # program_id from enrollment args
        else:
            factories.ProgramFactory(
                id=1,
                program_type=program_type,
                define_contractual_target_capacity=False,
            )
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        enrollment_req = EnrollmentController().create_enrollment_requests([enrollment_args])
        assert enrollment_req[0]["status"] == EnrollmentCRUDStatus.NOT_CREATED
        assert message.lower() in enrollment_req[0]["message"].lower()

    def test_get_one_enrollment(self, db_session, enrollment):
        program_id = enrollment.program_id
        got_enrollment = EnrollmentController().get_enrollment_request(enrollment.id)
        assert got_enrollment.program_id == program_id

    def test_get_all_enrollments(self, db_session):
        num_of_enrollments = 2
        factories.EnrollmentRequestFactory()
        factories.EnrollmentRequestFactory()
        enrollments = EnrollmentController().get_all_enrollment_requests()
        assert len(enrollments) == num_of_enrollments

    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit,check_der_eligibility,min_rating,max_rating",
        [
            pytest.param(
                100,
                LimitUnitType.kW,
                True,
                10,
                1000,
                id="min-max-criteria-pass",
            ),
            pytest.param(
                100,
                LimitUnitType.kW,
                True,
                None,
                1000,
                id="max-criteria-pass",
            ),
            pytest.param(
                100,
                LimitUnitType.kW,
                True,
                10,
                None,
                id="min-criteria-pass",
            ),
            pytest.param(
                100,
                LimitUnitType.kVAr,
                True,
                None,
                None,
                id="no-criteria-pass",
            ),
            pytest.param(
                100,
                LimitUnitType.kVAr,
                False,
                None,
                None,
                id="no-check-pass",
            ),
        ],
    )
    def test_create_enrollment_accepted(
        self,
        db_session,
        enrollment_dict,
        nameplate_rating,
        nameplate_rating_unit,
        check_der_eligibility,
        min_rating,
        max_rating,
    ):
        factories.ProgramFactory(
            id=enrollment_dict["general_fields"]["program_id"],
            check_der_eligibility=check_der_eligibility,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                min_real_power_rating=min_rating, max_real_power_rating=max_rating
            ),
        )
        factories.ServiceProviderFactory(
            id=enrollment_dict["general_fields"]["service_provider_id"]
        )
        factories.DerFactory(
            der_id=enrollment_dict["general_fields"]["der_id"],
            nameplate_rating=nameplate_rating,
            nameplate_rating_unit=nameplate_rating_unit,
            service_provider_id=enrollment_dict["general_fields"]["service_provider_id"],
        )

        # check there is no contract in the system
        contracts = self._get_all_contracts(db_session)
        assert len(contracts) == 0

        EnrollmentController().create_enrollment_requests([enrollment_dict])
        enrollments = self._get_all_enrollments(db_session)
        assert len(enrollments) == 1
        assert enrollments[0].rejection_reason is None
        assert enrollments[0].enrollment_status == EnrollmentRequestStatus.ACCEPTED

        # check there is one contract in the system
        contracts = self._get_all_contracts(db_session)
        assert len(contracts) > 0
        assert contracts[0].enrollment_request_id == enrollments[0].id

    @pytest.mark.parametrize(
        "nameplate_rating,nameplate_rating_unit,check_der_eligibility,min_rating,max_rating,no_der",
        [
            pytest.param(
                1,
                LimitUnitType.kW,
                True,
                10,
                1000,
                False,
                id="min-max-criteria-fail",
            ),
            pytest.param(
                90,
                LimitUnitType.MW,
                True,
                None,
                1000,
                False,
                id="max-criteria-fail",
            ),
            pytest.param(
                1,
                LimitUnitType.kW,
                True,
                10,
                None,
                False,
                id="min-criteria-fail",
            ),
            pytest.param(
                100,
                LimitUnitType.kVAr,
                True,
                10,
                900,
                False,
                id="no-info-available-fail",
            ),
            pytest.param(
                100,
                LimitUnitType.kW,
                False,
                None,
                None,
                True,
                id="der-not-associated-fail",
            ),
        ],
    )
    def test_create_enrollment_rejected(
        self,
        db_session,
        enrollment_dict,
        nameplate_rating,
        nameplate_rating_unit,
        check_der_eligibility,
        min_rating,
        max_rating,
        no_der,
    ):
        factories.ProgramFactory(
            id=enrollment_dict["general_fields"]["program_id"],
            check_der_eligibility=check_der_eligibility,
            resource_eligibility_criteria=ResourceEligibilityCriteria(
                min_real_power_rating=min_rating, max_real_power_rating=max_rating
            ),
        )
        factories.ServiceProviderFactory(
            id=enrollment_dict["general_fields"]["service_provider_id"]
        )
        if no_der:
            service_provider_id = None
        else:
            service_provider_id = enrollment_dict["general_fields"]["service_provider_id"]
        factories.DerFactory(
            der_id=enrollment_dict["general_fields"]["der_id"],
            nameplate_rating=nameplate_rating,
            nameplate_rating_unit=nameplate_rating_unit,
            service_provider_id=service_provider_id,
        )

        EnrollmentController().create_enrollment_requests([enrollment_dict])
        enrollments = self._get_all_enrollments(db_session)
        assert len(enrollments) == 1
        assert enrollments[0].enrollment_status == EnrollmentRequestStatus.REJECTED

    # Testing controller method while mocking minio put filhandle
    @freeze_time("2023-02-24 23:59:00")
    def test_enrollment_request_upload_controller(self, db_session):
        with patch("shared.minio_manager.MinioManager.put_filehandle") as mock_minio_manager:
            filename = "valid_enrollment_requests.csv"
            expected_file_name = "valid_enrollment_requests.2023-02-24T23-59-00-000000.csv"
            filepath = self._get_test_data_path(filename)
            factories.ProgramFactory(id=1)
            factories.ServiceProviderFactory(id=1)
            with open(filepath, "rb") as f:
                f_obj = FileStorage(f, filename)
                EnrollmentController().enrollment_request_upload(
                    1,
                    f_obj,
                    {"session_id": "session_id_123"},
                )
            mock_minio_manager.assert_called_once()
            args = mock_minio_manager.call_args.kwargs
            assert args["file_name"] == expected_file_name
            assert args["tags"] == {
                "original_file_name": filename,
                "program_id": "1",
                "FILE_TYPE": "EnrollmentRequest",
                "number_of_rows": "1",
                "session_id": "session_id_123",
            }

    @pytest.mark.parametrize(
        "program_id",
        [
            1,
            2,
            3,
        ],
    )
    def test_get_enrollment_report(self, db_session, program_id):
        program_1 = factories.ProgramFactory(id=1, name="program_1")
        program_2 = factories.ProgramFactory(id=2, name="program_2")
        factories.ProgramFactory(id=3, name="program_3")
        service_provider = factories.ServiceProviderFactory(id=1)
        der_1 = factories.DerFactory(der_id="der_1")
        der_2 = factories.DerFactory(der_id="der_2")
        der_3 = factories.DerFactory(der_id="der_3")
        factories.EnrollmentRequestFactory(
            id=1,
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
        )
        factories.EnrollmentRequestFactory(
            id=2,
            program=program_1,
            service_provider=service_provider,
            der=der_2,
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            created_at=datetime(2022, 11, 8, tzinfo=timezone.utc),
        )
        factories.EnrollmentRequestFactory(
            id=3,
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            created_at=datetime(2022, 11, 9, tzinfo=timezone.utc),
        )
        factories.EnrollmentRequestFactory(
            id=4,
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.PENDING,
            created_at=datetime(2022, 11, 10, tzinfo=timezone.utc),
        )
        factories.EnrollmentRequestFactory(
            id=5,
            program=program_2,
            service_provider=service_provider,
            der=der_3,
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            created_at=datetime(2022, 11, 11, tzinfo=timezone.utc),
        )
        with patch(
            "pm.modules.enrollment.services.enrollment.EnrollmentService.create_enrollment_report"
        ) as create_enrollment_report:
            EnrollmentController().get_enrollment_report(program_id)
            create_enrollment_report.assert_called_once()
            args = create_enrollment_report.call_args[0][0]
            if program_id == 1:
                assert len(args) == 2
                assert args[0].id == 3
                assert args[1].id == 2
            if program_id == 2:
                assert len(args) == 1
                assert args[0].id == 5
            if program_id == 3:
                assert len(args) == 0

    def test_get_enrollment_report_fail(self, db_session):
        with pytest.raises(ProgramNotFound):
            EnrollmentController().get_enrollment_report(100)
