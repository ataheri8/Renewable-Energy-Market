from http import HTTPStatus

from pm.tests_acceptance.mixins import TestDataMixin


class TestPM888(TestDataMixin):
    """As a user, I need to be able to request a template to bulk upload"""

    def test_download_service_provider_csv_template(self, client):
        """BDD PM-924

         Given User wants to download ServiceProvicer csv template
        When User hits GET /api/serviceprovider/download_service_provider_template endpoint
        Then the user receives a 200 (OK) status
        And a csv is download with one row with the following headers
        Name,Type,Primary contact,Primary email,Notification contact,Notification email,
        Street Address,Apt/unit,City,State/Province/Region,Country,ZIP/Postal Code,Status
        """

        expected_template = (
            "Name,Type,Primary contact,Primary email,Notification contact,Notification email,"
            "Street Address,Apt/unit,City,State/Province/Region,Country,ZIP/Postal Code,Status\r\n"
        )
        resp = client.get("api/serviceprovider/download_service_provider_template")
        assert resp.status_code == HTTPStatus.OK
        assert resp.data.decode("utf-8-sig") == expected_template

    def test_download_service_provider_der_association_csv_template(self, client):
        """BDD PM-925

        Given User wants to download ServiceProvider DER association csv template
        When User hits GET /api/serviceprovider/download_der_association_template endpoint
        Then the user receives a 200 (OK) status
        And a csv is download with one row with the following headers
        |der_rdf_id|
        """

        expected_template = "der_id\r\n"
        resp = client.get("api/serviceprovider/download_der_association_template")
        assert resp.status_code == HTTPStatus.OK
        assert resp.data.decode("utf-8-sig") == expected_template
