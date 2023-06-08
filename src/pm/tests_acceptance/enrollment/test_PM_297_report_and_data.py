from http import HTTPStatus

from pm.modules.enrollment.enums import (
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


class TestPM297(TestDataMixin):
    """As a user, I need a full list of currently-enrolled DER for a particular program and their
    enrollment status so that I can see which DER have been rejected and why.
    """

    def test_enrollment_report_program_does_not_exist(self, client, db_session):
        """BDD PM-792

        Given a program with id program_id does not exist in pm database
        When a report is requested for that program_id
        Then user receives a 404 (NOT_FOUND) response to their request
        """
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_enrollment_report_program_has_no_enrollments(self, client, db_session):
        """BDD PM-793

        Given a program exists in the pm database
        And no enrollment requests have been submitted for that program
        When a report is requested for that program
        Then user receives a 200 OK status code
        And the csv that is downloaded is empty except for the headers
        """
        factories.ProgramFactory(id=1)
        filepath = self._get_test_data_path("enrollment_report_empty.csv")
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.OK
        with open(filepath, "rb") as file:
            assert resp.data == file.read()

    def test_enrollment_report_program_has_pending_enrollments(self, client, db_session):
        """BDD PM-794

        Given a program exists in the pm database
        And some enrollment requests have been submitted for that program but are pending
        When a report is requested for that program
        Then user receives a 200 OK status code
        And the csv that is downloaded is empty except for the headers
        """
        program = factories.ProgramFactory(id=1)
        service_provider = factories.ServiceProviderFactory(id=1)
        der_1 = factories.DerFactory(der_id="der_1")
        factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider,
            der_id=der_1.der_id,
            enrollment_status=EnrollmentRequestStatus.PENDING,
        )
        filepath = self._get_test_data_path("enrollment_report_empty.csv")
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.OK
        with open(filepath, "rb") as file:
            assert resp.data == file.read()

    def test_enrollment_report_program_has_enrollments(self, client, db_session):
        """BDD PM-797

        Given a program exists in the pm database
        And some enrollment requests have been submitted for that program
        When a report is requested for that program
        Then user receives a 200 OK status code
        And the csv that is downloaded is populated with data
        And the statuses of the enrollment requests in the report are ACCEPTED or REJECTED only
        """
        program_1 = factories.ProgramFactory(id=1, name="program_1")
        program_2 = factories.ProgramFactory(id=2, name="program_2")
        service_provider = factories.ServiceProviderFactory(id=1)
        der_1 = factories.DerFactory(der_id="der_1")
        der_2 = factories.DerFactory(der_id="der_2")
        der_3 = factories.DerFactory(der_id="der_3")
        # in report
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            rejection_reason=EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND,
            created_at="2022-11-07T00:00:00+00:00",
        )
        # not in report because different program
        factories.EnrollmentRequestFactory(
            program=program_2,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            rejection_reason=EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA,
        )
        # in report
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_2,
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            rejection_reason=None,
            created_at="2022-11-07T06:21:59+00:00",
        )
        # not in report because status is pending
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_3,
            enrollment_status=EnrollmentRequestStatus.PENDING,
            rejection_reason=None,
        )
        filepath = self._get_test_data_path("enrollment_report_populated.csv")
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.OK
        with open(filepath, "rb") as file:
            assert resp.data == file.read()

    def test_enrollment_report_overwritten_enrollments(self, client, db_session):
        """BDD PM-798

        Given a program exists in the pm database
        And multiple enrollment requests for the same DER/Service Provider have been made
        When a report is requested for that program
        Then user receives a 200 OK status code
        And the csv that is downloaded only has the most recent enrollment request
        """
        program_1 = factories.ProgramFactory(id=1, name="program_1")
        program_2 = factories.ProgramFactory(id=2, name="program_2")
        service_provider = factories.ServiceProviderFactory(id=1)
        der_1 = factories.DerFactory(der_id="der_1")
        der_2 = factories.DerFactory(der_id="der_2")
        der_3 = factories.DerFactory(der_id="der_3")
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            rejection_reason=EnrollmentRejectionReason.ELIGIBILITY_DATA_NOT_FOUND,
            created_at="2022-11-07T00:00:00+00:00",
        )
        factories.EnrollmentRequestFactory(
            program=program_2,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            rejection_reason=EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA,
        )
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_2,
            enrollment_status=EnrollmentRequestStatus.ACCEPTED,
            rejection_reason=None,
            created_at="2022-11-07T06:21:59+00:00",
        )
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_3,
            enrollment_status=EnrollmentRequestStatus.PENDING,
            rejection_reason=None,
        )
        factories.EnrollmentRequestFactory(
            program=program_1,
            service_provider=service_provider,
            der=der_1,
            enrollment_status=EnrollmentRequestStatus.REJECTED,
            rejection_reason=EnrollmentRejectionReason.DER_DOES_NOT_MEET_CRITERIA,
            created_at="2022-11-08T00:06:00+00:00",
        )
        filepath = self._get_test_data_path("enrollment_report_overwritten.csv")
        resp = client.get("/api/enrollment/report/program/1")
        assert resp.status_code == HTTPStatus.OK
        assert (
            resp.headers.get("Content-Disposition")
            == "attachment; filename=enrollment_report_program_1.csv"
        )
        with open(filepath, "rb") as file:
            assert resp.data == file.read()
