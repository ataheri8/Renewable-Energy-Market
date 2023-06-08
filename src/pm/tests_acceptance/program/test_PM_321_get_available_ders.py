from pm.tests import factories


class TestPM321:
    """As a program admin, I need to select DER to enroll in my program so that I can
    create contracts and dispatch them, to ultimately ensure my program is successful."""

    def test_get_available_ders(self, client, db_session):
        program = factories.ProgramFactory()
        program_id = program.id
        program_2 = factories.ProgramFactory()
        program_2_id = program_2.id
        enrollment_request_id = 1
        enrollment_request_id_2 = 2
        service_provider_id = 1

        # Without any data, should return 0

        resp = client.get(f"/api/program/{program_id}/available_ders")

        assert len(resp.json) == 0

        factories.ServiceProviderFactory(id=service_provider_id)
        factories.DerFactory(
            service_provider_id=service_provider_id,
            der_id="123",
        ),
        factories.DerFactory(
            service_provider_id=service_provider_id,
            der_id="234",
        ),

        factories.EnrollmentRequestFactory(id=enrollment_request_id, der_id="123")
        factories.EnrollmentRequestFactory(id=enrollment_request_id_2, der_id="234")
        factories.ContractFactory(
            enrollment_request_id=enrollment_request_id,
            program_id=program_id,
            service_provider_id=service_provider_id,
            der_id="123",
        )
        factories.ContractFactory(
            enrollment_request_id=enrollment_request_id_2,
            program_id=program_2_id,
            service_provider_id=service_provider_id,
            der_id="234",
        )

        resp = client.get(f"/api/program/{program_id}/available_ders")

        assert len(resp.json) == 2
        for der_id in resp.json:
            assert der_id["der_id"] in ["123", "234"]

    def test_get_enrollments(self, client, db_session):
        program = factories.ProgramFactory()
        program_id = program.id
        program2 = factories.ProgramFactory()
        program2_id = program2.id
        service_provider = factories.ServiceProviderFactory()
        service_provider_id = service_provider.id

        # Without any data, should return 0

        resp = client.get(f"/api/program/{program_id}/enrollments")

        assert len(resp.json) == 0

        factories.DerFactory(
            service_provider_id=service_provider_id,
            der_id="123",
        ),
        factories.DerFactory(
            service_provider_id=service_provider_id,
            der_id="234",
        ),
        factories.DerFactory(
            service_provider_id=service_provider_id,
            der_id="345",
        ),

        factories.EnrollmentRequestFactoryWithProgramAndServiceProvider(
            der_id="123", program_id=program_id, service_provider_id=service_provider_id
        )
        factories.EnrollmentRequestFactoryWithProgramAndServiceProvider(
            der_id="234", program_id=program_id, service_provider_id=service_provider_id
        )
        factories.EnrollmentRequestFactoryWithProgramAndServiceProvider(
            der_id="345", program_id=program2_id, service_provider_id=service_provider_id
        )

        # Expect 0 because the DER's are all assigned to other programs

        resp = client.get(f"/api/program/{program_id}/enrollments")

        assert len(resp.json) == 2
