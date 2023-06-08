from http import HTTPStatus

import pytest
from testfixtures import LogCapture

from pm.modules.enrollment.controller import EnrollmentController
from pm.tests import factories
from shared.enums import ProgramTypeEnum


class TestPM322:
    """[Enrollment] Enroll list of DERs through API"""

    @pytest.mark.parametrize(
        "body,program_type,response",
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
                        export_target_capacity=300.01,
                    ),
                ),
                ProgramTypeEnum.DEMAND_MANAGEMENT,
                "CREATED",
                id="all-fields",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    )
                ),
                ProgramTypeEnum.GENERIC,
                "CREATED",
                id="minimum-fields",
            ),
        ],
    )
    def test_create_enrollment_single_der_success(
        self, client, db_session, body, program_type, response
    ):
        """BDD Scenario: PM-583

        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing single enrollment's fields data as
        json object nested in a list
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response Body should be list of created new enrollments with one field
        specifying it's id
        """
        factories.ProgramFactory(id=1, program_type=program_type)
        factories.ServiceProviderFactory(id=1)
        factories.DerFactory(der_id="test der id")
        resp = client.post("/api/enrollment/", json=[body])
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == response

    @pytest.mark.parametrize(
        "body,response",
        [
            pytest.param(
                [
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
                            export_target_capacity=300.01,
                        ),
                    ),
                    dict(
                        general_fields=dict(
                            program_id=2,
                            service_provider_id=1,
                            der_id="test der id",
                        )
                    ),
                ],
                "CREATED",
            ),
        ],
    )
    def test_create_enrollment_multiple_ders_success(self, client, db_session, body, response):
        """BDD Scenario: PM-653

        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing multiple enrollments' fields data as
        json objects nested in a list
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response Body should be list of created new enrollments with one field
        specifying it's id
        """
        factories.ProgramFactory(id=1, program_type=ProgramTypeEnum.DEMAND_MANAGEMENT)
        factories.ProgramFactory(id=2, program_type=ProgramTypeEnum.GENERIC)
        factories.DerFactory(der_id="test der id")
        factories.ServiceProviderFactory(id=1)
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == response
        assert resp.json[1]["status"] == response

    @pytest.mark.parametrize(
        "body,program_type,define_contractual_target_capacity,response,message,http_code",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Active Power Import (kW) should be provided",
                HTTPStatus.CREATED,
                id="dynamic_operating_envelopes_param_incorrect-1a",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                    dynamic_operating_envelopes=dict(
                        default_limits_active_power_import_kw=-50,
                        default_limits_active_power_export_kw=50,
                        default_limits_reactive_power_import_kw=50,
                        default_limits_reactive_power_export_kw=50,
                    ),
                ),
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Active Power Import (kW) should not be negative",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Active Power Export (kW) should be provided",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Active Power Export (kW) should not be negative",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Reactive Power Import (kW) should be provided",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Reactive Power Import (kW) should not be negative",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Reactive Power Export (kW) should be provided",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES,
                False,
                "NOT_CREATED",
                "Reactive Power Export (kW) should not be negative",
                HTTPStatus.CREATED,
                id="dynamic_operating_envelopes_param_incorrect-4b",
            ),
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=1,
                        der_id="test der id",
                    ),
                ),
                ProgramTypeEnum.DEMAND_MANAGEMENT,
                True,
                "NOT_CREATED",
                "Enrollment Request program has define_contractual_target_capacity "
                "set to True but it is missing contractual target capacity",
                HTTPStatus.CREATED,
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
                ProgramTypeEnum.GENERIC,
                True,
                "NOT_CREATED",
                "Enrollment Request program has define_contractual_target_capacity "
                "set to True but it is missing contractual target capacity",
                HTTPStatus.CREATED,
                id="generic",
            ),
        ],
    )
    def test_create_enrollment_not_created_error(
        self,
        client,
        db_session,
        body,
        program_type,
        define_contractual_target_capacity,
        http_code,
        response,
        message,
    ):
        """BDD scenarios PM-669, PM-670

        Given the user is a program admin
        And there is already a program created on the platform with id 1
        And there is already a service provider created on the platform with id 1
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing single enrollment's fields with program type DOE
        And at least one of the default limit missing
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response object should have a json field which would have an status as "NOT_CREATED"
        and a proper message indicating the proper reason
        """
        factories.ProgramFactory(
            id=1,
            program_type=program_type,
            define_contractual_target_capacity=define_contractual_target_capacity,
        )
        factories.ServiceProviderFactory(id=1)
        factories.DerFactory(der_id="test der id")
        resp = client.post("/api/enrollment/", json=[body])
        assert resp.status_code == http_code
        assert resp.json[0]["status"] == response
        assert message.lower() in resp.json[0]["message"].lower()

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
        """BDD scenarios PM-671

        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing single enrollment's fields data
        as json object nested in a list
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response Body should be list of created new enrollments with one field
        specifying it's id
        And it can be checked that a "Enrollment Request Created" event has
        been triggered either by checking logs or newly created event information
        """
        factories.ProgramFactory(id=1)  # program_id from enrollment args
        factories.ServiceProviderFactory(id=1)  # service_provider_id from enrollment args
        factories.DerFactory(der_id="test der id")
        with LogCapture() as logs:
            EnrollmentController().create_enrollment_requests([enrollment_args])
        assert "Created Enrollment Request" in str(logs)

    @pytest.mark.parametrize(
        "body,message",
        [
            pytest.param(
                dict(
                    general_fields=dict(
                        program_id=1,
                        service_provider_id=2,
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
                        export_target_capacity=300.01,
                    ),
                ),
                "Service Provider with id 2 is not found",
            )
        ],
    )
    def test_create_enrollment_failure_service_provder_not_found(
        self, client, db_session, body, message
    ):
        """BDD scenarios PM-679

        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is not a service provider created on the plateform with id 1
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing single enrollment's fields
        with the service_provider_id field as 2
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response object should have a json field which would have an status
        as "NOT_CREATED" and a proper message indicating the proper reason
        """
        factories.ProgramFactory(id=1)
        factories.ServiceProviderFactory(id=1)
        resp = client.post("/api/enrollment/", json=[body])
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "NOT_CREATED"
        assert message.lower() in resp.json[0]["message"].lower()

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                [
                    dict(
                        general_fields=dict(
                            program_id=1,
                            service_provider_id=1,
                            der_id="test der id",
                        ),
                        demand_response=dict(
                            import_target_capacity=300.01,
                            export_target_capacity=300.01,
                        ),
                    ),
                    dict(
                        general_fields=dict(
                            program_id=2,
                            service_provider_id=1,
                            der_id="test der id",
                        ),
                        dynamic_operating_envelopes=dict(
                            default_limits_active_power_import_kw=-50,
                            default_limits_active_power_export_kw=50,
                            default_limits_reactive_power_import_kw=50,
                            default_limits_reactive_power_export_kw=50,
                        ),
                    ),
                ]
            ),
        ],
    )
    def test_create_enrollment_multiple_ders_some_success_other_fail(
        self, client, db_session, body
    ):
        """BDD scenarios PM-681

        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1
        And there is not a service provider created on the plateform with id 2
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing multiple enrollments' fields
        data as json objects nested in a list
        And one of the DER enrollment request has Service Provider id 1 and
        another has service provider id 2
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response Body should be list of created new enrollments with one
        field specifying it's id
        And the DER enrollment request belonging to service provider id 1 is
        successfull but request belonging to id 2 is not successful
        """
        factories.ProgramFactory(id=1, program_type=ProgramTypeEnum.DEMAND_MANAGEMENT)
        factories.ProgramFactory(id=2, program_type=ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES)
        factories.ServiceProviderFactory(id=1)
        factories.DerFactory(der_id="test der id")
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "CREATED"
        assert resp.json[1]["status"] == "NOT_CREATED"

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                [
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
                            export_target_capacity=300.01,
                        ),
                    ),
                    dict(
                        general_fields=dict(
                            program_id=1,
                            service_provider_id=2,
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
                            export_target_capacity=300.01,
                        ),
                    ),
                ],
            )
        ],
    )
    def test_create_enrollment_ability_valid_ders_with_invalid_ders(self, client, db_session, body):
        """BDD scenarios PM-681

        Given the user is a program admin
        And there is already a program created on the plateform with id 1
        And there is already a service provider created on the plateform with id 1
        And there is not a service provider created on the plateform with id 2
        And the user sets POST request endpoint  /api/enrollment
        And the user sets Request Body containing multiple enrollments' fields
        data as json objects nested in a list
        And one of the DER enrollment request has Service Provider id 1 and
        another has service provider id 2
        When the user Sends POST Request
        Then the user receives HTTP Response code 201
        And Response Body should be list of created new enrollments with one
        field specifying it's id
        And the DER enrollment request belonging to service provider id 1 is successful
        but request belonging to id 2 is not successful
        """
        factories.ProgramFactory(id=1)
        factories.ServiceProviderFactory(id=1)
        factories.DerFactory(der_id="test der id")
        resp = client.post("/api/enrollment/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.json[0]["status"] == "CREATED"
        assert resp.json[1]["status"] == "NOT_CREATED"
