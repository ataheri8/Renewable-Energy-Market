from datetime import datetime, timedelta

from faker import Faker

from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase


class TestPM944(TestProgramBase):
    """[Program Manager - Event Dispatch] As a user, I need the ability to
    generate a report for my program
    """

    def test_create_report(self, client, db_session):
        """Given a user wants to generate a new program report
        When a user fills out the report UI and hits submit
        Then a report is generated for the program and dates specified
        """
        fake = Faker()
        program = factories.ProgramFactory(id=2)
        factories.DerFactory(id=10)
        factories.ServiceProviderFactory(id=10)
        factories.ContractFactory(
            id=10,
            program=program,
            demand_response={"import_target_capacity": 10, "export_target_capacity": 10},
        )
        factories.ContractConstraintSummaryFactory(id=10, contract_id=10)
        factories.DerDispatchFactory(contract_id=10, cumulative_event_duration_mins=200)
        factories.DerResponseFactory()

        fake_name = fake.name()

        body = dict(
            report_type="INDIVIDUAL_PROGRAM",
            program_id=2,
            service_provider_id=fake.random_int(0, 100),
            start_report_date=fake.date_time_between(
                datetime.strptime("2023-01-01", "%Y-%m-%d"),
                datetime.strptime("2023-01-10", "%Y-%m-%d"),
            ).isoformat(),
            end_report_date=fake.date_time_between(
                datetime.strptime("2023-02-01", "%Y-%m-%d"),
                datetime.strptime("2023-02-10", "%Y-%m-%d"),
            ).isoformat(),
            created_by=fake_name,
        )
        resp = client.post("/api/reports", json=body)
        assert resp.status_code == 201

        factories.ContractReportDetailsFactory(
            contract_constraint_id=10, report_id=1, der_id=10, service_provider_id=10
        )
        factories.EventDetailsFactory(report_id=1)

        report = (client.get("/api/reports/1/summary")).json
        assert report is not None
        assert report["report_type"] == "INDIVIDUAL_PROGRAM"
        assert report["program_id"] == 2
        assert report["created_by"] == fake_name
        assert report["total_events"] == 1
        assert report["average_event_duration"] == 3

    def test_create_report_missing_data_error(self, client, db_session):
        """Given a user wants to generate a new program report
        When a user submits incomplete data
        Then a 422 error should be returned outlining the missing fields
        """
        fake = Faker()
        factories.ProgramFactory(id=1)
        body = dict(
            report_type="INDIVIDUAL_PROGRAM",
            start_report_date=fake.date_time_between(
                datetime.strptime("2023-01-01", "%Y-%m-%d"),
                datetime.strptime("2023-01-10", "%Y-%m-%d"),
            ).isoformat(),
            end_report_date=fake.date_time_between(
                datetime.strptime("2023-02-01", "%Y-%m-%d"),
                datetime.strptime("2023-02-10", "%Y-%m-%d"),
            ).isoformat(),
            created_by=fake.name(),
        )
        resp = client.post("/api/reports", json=body)
        assert resp.status_code == 422

    def test_create_report_future_date_error(self, client, db_session):
        """Given a user wants to generate a new program report
        When a user enters a date in the future
        Then a 422 error should be returned outlining that dates need to be in the past
        """
        fake = Faker()
        factories.ProgramFactory(id=1)
        body = dict(
            report_type="INDIVIDUAL_PROGRAM",
            program_id=1,
            service_provider_id=fake.random_int(0, 100),
            start_report_date=fake.date_time_between(
                datetime.strptime("2023-01-01", "%Y-%m-%d"),
                datetime.strptime("2023-01-10", "%Y-%m-%d"),
            ).isoformat(),
            end_report_date=fake.date_time_between(
                datetime.now() + timedelta(days=1),
                datetime.now() + timedelta(days=5),
            ).isoformat(),
            created_by=fake.name(),
        )
        resp = client.post("/api/reports", json=body)
        assert resp.status_code == 422

    def test_create_report_invalid_program_error(self, client, db_session):
        """Given a user wants to generate a new program report
        When a user fills out the report UI and hits submit and there is no program
        Then a 400 error is thrown
        """
        fake = Faker()
        body = dict(
            report_type="INDIVIDUAL_PROGRAM",
            program_id=fake.random_int(0, 100),
            service_provider_id=fake.random_int(0, 100),
            start_report_date=fake.date_time_between(
                datetime.strptime("2023-01-01", "%Y-%m-%d"),
                datetime.strptime("2023-01-10", "%Y-%m-%d"),
            ).isoformat(),
            end_report_date=fake.date_time_between(
                datetime.strptime("2023-02-01", "%Y-%m-%d"),
                datetime.strptime("2023-02-10", "%Y-%m-%d"),
            ).isoformat(),
            created_by=fake.name(),
        )
        resp = client.post("/api/reports", json=body)
        assert resp.status_code == 400
