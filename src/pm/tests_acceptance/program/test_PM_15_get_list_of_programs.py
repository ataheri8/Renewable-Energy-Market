from datetime import datetime, timezone

from pm.modules.progmgmt.enums import AvailabilityType, ProgramCategory, ProgramStatus
from pm.modules.progmgmt.models.avail_operating_months import AvailOperatingMonths
from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase
from shared.enums import ProgramTypeEnum
from shared.system import configuration


class TestPM15(TestProgramBase):
    """As a utility, I need to see a list of programs"""

    def test_get_empty_program_list(self, client, db_session):
        resp = client.get("/api/program/")
        assert resp.status_code == 200
        assert len(resp.json["results"]) == 0

    def test_get_program_list(self, client, db_session):
        expected = [
            {
                "id": 3,
                "name": "test program 2",
                "program_type": "GENERIC",
                "status": "ACTIVE",
                "start_date": "2022-11-08T00:00:00+00:00",
                "end_date": "2023-11-02T00:00:00+00:00",
                "created_at": "2022-11-07T00:00:00+00:00",
            },
            {
                "id": 1,
                "name": "test program 1",
                "program_type": "GENERIC",
                "status": "ACTIVE",
                "start_date": "2022-11-09T00:00:00+00:00",
                "end_date": "2023-11-01T00:00:00+00:00",
                "created_at": "2022-11-06T00:00:00+00:00",
            },
        ]
        factories.ProgramFactory(
            name="test program 1",
            program_type=ProgramTypeEnum.GENERIC,
            program_category=ProgramCategory.LIMIT_BASED,
            availability_type=AvailabilityType.ALWAYS_AVAILABLE,
            status=ProgramStatus.ACTIVE,
            avail_operating_months=AvailOperatingMonths(
                jan=True,
                feb=True,
                mar=True,
                apr=True,
                may=True,
                jun=True,
                jul=True,
                aug=True,
                sep=True,
                oct=True,
                nov=True,
                dec=True,
            ),
            created_at=datetime(2022, 11, 6, tzinfo=timezone.utc),
            start_date=datetime(2022, 11, 9, tzinfo=timezone.utc),
            end_date=datetime(2023, 11, 1, tzinfo=timezone.utc),
            program_priority="P0",
            check_der_eligibility=True,
        )
        factories.ProgramFactory(
            name="not finished program 1",
            program_type=ProgramTypeEnum.DEMAND_MANAGEMENT,
            program_category=ProgramCategory.TARGET_BASED,
            availability_type=AvailabilityType.SERVICE_WINDOWS,
            status=ProgramStatus.DRAFT,
            avail_operating_months=AvailOperatingMonths(
                jan=True,
                feb=True,
                mar=True,
                apr=True,
                may=True,
                jun=True,
                jul=True,
                aug=True,
                sep=True,
                oct=True,
                nov=True,
                dec=True,
            ),
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
            program_priority="P0",
            check_der_eligibility=True,
        )
        factories.ProgramFactory(
            name="test program 2",
            program_type=ProgramTypeEnum.GENERIC,
            program_category=ProgramCategory.LIMIT_BASED,
            availability_type=AvailabilityType.ALWAYS_AVAILABLE,
            status=ProgramStatus.ACTIVE,
            avail_operating_months=AvailOperatingMonths(
                jan=True,
                feb=True,
                mar=True,
                apr=True,
                may=True,
                jun=True,
                jul=True,
                aug=True,
                sep=True,
                oct=True,
                nov=True,
                dec=True,
            ),
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
            start_date=datetime(2022, 11, 8, tzinfo=timezone.utc),
            end_date=datetime(2023, 11, 2, tzinfo=timezone.utc),
            program_priority="P0",
            check_der_eligibility=True,
        )
        factories.ProgramFactory(
            name="not finished program 2",
            program_type=ProgramTypeEnum.GENERIC,
            program_category=ProgramCategory.TARGET_BASED,
            availability_type=AvailabilityType.SERVICE_WINDOWS,
            status=ProgramStatus.DRAFT,
            avail_operating_months=AvailOperatingMonths(
                jan=True,
                feb=True,
                mar=True,
                apr=True,
                may=True,
                jun=True,
                jul=True,
                aug=True,
                sep=True,
                oct=True,
                nov=True,
                dec=True,
            ),
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
            start_date=datetime(2022, 11, 10, tzinfo=timezone.utc),
            end_date=datetime(2023, 11, 5, tzinfo=timezone.utc),
            program_priority="P0",
            check_der_eligibility=True,
        )
        factories.ProgramFactory(
            name="test program 3",
            program_type=ProgramTypeEnum.GENERIC,
            program_category=ProgramCategory.LIMIT_BASED,
            availability_type=AvailabilityType.ALWAYS_AVAILABLE,
            status=ProgramStatus.ACTIVE,
            avail_operating_months=AvailOperatingMonths(
                jan=True,
                feb=True,
                mar=True,
                apr=True,
                may=True,
                jun=True,
                jul=True,
                aug=True,
                sep=True,
                oct=True,
                nov=True,
                dec=True,
            ),
            created_at=datetime(2022, 11, 7, tzinfo=timezone.utc),
            start_date=datetime(2022, 11, 8, tzinfo=timezone.utc),
            end_date=datetime(2023, 11, 24, tzinfo=timezone.utc),
            program_priority="P0",
            check_der_eligibility=True,
        )

        params = {
            "program_type": "GENERIC",
            "status": "ACTIVE",
            "start_date": "2022-11-08T00:00:00+00:00",
            "end_date": "2023-11-08T00:00:00+00:00",
            "order_by": "CREATED_AT",
            "order_type": "DESC",
        }
        resp = client.get("/api/program/", query_string=params)
        assert resp.status_code == 200
        assert len(resp.json["results"]) == 2
        assert resp.json["results"] == expected
        assert resp.json["count"] == 2
        assert resp.json["pagination_start"] == 1
        assert resp.json["pagination_end"] == configuration.get_config().PAGINATION_DEFAULT_LIMIT

    def test_non_exist_program(self, client):
        resp = client.get("/api/program/1")
        assert resp.status_code == 404
        assert resp.json["message"] == "program with ID 1 not found"

        resp = client.delete("/api/program/1")
        assert resp.status_code == 404
        assert resp.json["message"] == "program with ID 1 not found"
