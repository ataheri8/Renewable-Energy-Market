from datetime import date
from http import HTTPStatus

from pm.tests import factories


class TestPM629:
    """We must be able to query an endpoint to get information about our contract
    and the tracked contract constraints."""

    def test_get_constraints_valid_data(self, client, db_session):
        """BDD PM-761

        Given a contract was created and it's processed constraints are existed
        When fetch the processed constraint by the contract ID
        Then it should return the processed constraints according to AC specs
        """
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        factories.ContractConstraintSummaryFactory(
            day=date(2023, 4, 25),
            contract_id=contract_id,
            cumulative_event_duration_day=10,
            cumulative_event_duration_day_violation=True,
            cumulative_event_duration_week=20,
            cumulative_event_duration_week_violation=False,
            cumulative_event_duration_program_duration=50,
            cumulative_event_duration_program_duration_violation=False,
            opt_outs_day=5,
            opt_outs_day_violation=True,
        )
        resp = client.get("/api/contract/1/constraints")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json["cumulative_event_duration"] == {
            "DAY": {
                "number": 10,
                "violation": True,
            },
            "WEEK": {
                "number": 20,
                "violation": False,
            },
            "PROGRAM_DURATION": {"number": 50, "violation": False},
        }

        assert resp.json["opt_outs"] == {
            "DAY": {
                "number": 5,
                "violation": True,
            }
        }

    def test_get_constraints_404(self, client, db_session):
        """BDD PM-762
        Given contract doesn't exist
        When fetch a processed constraints by not existing contract ID
        Then it should return 404 status code
        """
        resp = client.get("/api/contract/1/constraints")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_get_constraints_empty_data(self, client, db_session):
        """BDD PM-767

        Given a contract was created and it's processed constraints are not existed
        When fetch the processed constraints by the contract ID
        Then it should return 200 status code but return empty json response({})"""
        contract_id = 1
        factories.ContractFactory(id=contract_id)
        resp = client.get("/api/contract/1/constraints")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json == {}
