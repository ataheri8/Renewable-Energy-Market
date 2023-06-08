from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session as S

from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.reports.controller import ReportController
from pm.modules.reports.enums import ReportTypeEnum
from pm.modules.reports.services.report import CreateReport
from pm.tests import factories
from shared.system.database import Session


class TestReportController:
    def _get_contract_constraint(self, contract_constraint_id: int) -> ContractConstraintSummary:
        s: S
        with Session() as s:
            return s.query(ContractConstraintSummary).get(contract_constraint_id)

    @pytest.mark.parametrize(
        "report_args",
        [
            pytest.param(
                dict(
                    report_type=ReportTypeEnum.INDIVIDUAL_PROGRAM,
                    program_id=10,
                    service_provider_id=1,
                    start_report_date=datetime.now() - timedelta(days=2),
                    end_report_date=datetime.now() + timedelta(days=1),
                    created_by="Tom Brady",
                )
            )
        ],
    )
    def test_create_report(self, db_session, report_args):
        program = factories.ProgramFactory(id=10)
        report_data = CreateReport.from_dict(report_args)

        factories.ServiceProviderFactory(id=10)
        factories.ContractFactory(
            id=10,
            program=program,
            demand_response={"import_target_capacity": 10, "export_target_capacity": 10},
        )
        factories.ContractConstraintSummaryFactory(
            id=10, contract_id=10, cumulative_event_duration_week=30
        )

        # opted out event
        factories.DerDispatchFactory(
            control_id=1,
            contract_id=10,
            start_date_time=datetime.now() - timedelta(days=1),
            end_date_time=datetime.now(),
            cumulative_event_duration_mins=200,
        )
        factories.DerResponseFactory(is_opt_out=True, control_id=1)
        # dispatched event
        factories.DerDispatchFactory(
            control_id=2,
            contract_id=10,
            start_date_time=datetime.now() - timedelta(days=1),
            end_date_time=datetime.now(),
            cumulative_event_duration_mins=400,
        )
        factories.DerResponseFactory(is_opt_out=False, control_id=2)
        factories.DerFactory(id=10)

        ReportController().create_report(report_data)

        factories.ContractReportDetailsFactory(
            contract_constraint_id=10, report_id=1, der_id=10, service_provider_id=10
        )

        factories.EventDetailsFactory(report_id=1)

        contract_report_object = ReportController().get_contract_report_details(
            {
                "pagination_start": 1,
                "pagination_end": 2,
                "report_id": 1,
                "order_type": "asc",
            }
        )

        event_report_object = ReportController().get_event_report_details(
            {
                "report_id": 1,
                "pagination_start": 1,
                "pagination_end": 2,
                "order_type": "asc",
            }
        )

        contract_constraint_object = self._get_contract_constraint(
            contract_report_object.results[0].contract_constraint_id
        )

        assert contract_report_object.count == 2
        assert contract_constraint_object.cumulative_event_duration_week == 30
        assert event_report_object.count == 3
        assert event_report_object.results[0].number_of_opted_out_der == 1
        assert event_report_object.results[1].number_of_dispatched_der == 1

        get_report = ReportController().get_report(report_id=1)

        assert get_report
        assert get_report.service_provider_id == 1
        assert get_report.total_events == 2
        assert get_report.average_event_duration == 5

    def test_get_report(self, db_session):
        report = factories.ReportFactory()
        report_id = report.id

        get_report = ReportController().get_report(report_id)

        assert get_report

    def test_get_all_reports(self, db_session):
        factories.ReportFactory(id=1)
        factories.ReportFactory(id=2)
        factories.ReportFactory(id=3)

        get_report = ReportController().get_all_reports()

        assert get_report
        assert len(get_report) == 3
