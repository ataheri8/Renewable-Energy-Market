from http import HTTPStatus

from pm.tests_acceptance.mixins import TestDataMixin


class TestPM887(TestDataMixin):
    """As a user, I need to be able to request a template to bulk upload enrollment requests"""

    def test_enrollment_request_csv_template_download(self, client):
        """BDD PM-922

        When a user requests a template for bulk enrollment upload
        Then the user receives a 200 (OK) status
        And a csv is download with one row with the following headers
        |DER_ID,Import Target capacity (kW) (optional),Export Target Capacity (kW)(optional),
        Default Limits - Active Power Import (kW) (optional),Default Limits - Active Power Export
        (kW) (optional),Default Limits - Reactive Power Import (kW) (optional),Default Limits -
        Reactive Power Export (kW) (optional)|
        """

        expected_template = (
            "DER_ID,Import Target capacity (kW) (optional),Export Target Capacity (kW) "
            "(optional),Default Limits - Active Power Import (kW) (optional),Default "
            "Limits - Active Power Export (kW) (optional),Default Limits - Reactive Power "
            "Import (kW) (optional),Default Limits - Reactive Power Export (kW) "
            "(optional)\r\n"
        )
        resp = client.get("/api/enrollment/download_template")
        assert resp.status_code == HTTPStatus.OK
        assert resp.data.decode("utf-8-sig") == expected_template
