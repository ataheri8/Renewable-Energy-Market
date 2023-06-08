import requests  # type: ignore
from requests.exceptions import HTTPError, RequestException  # type: ignore

from shared.system import configuration, loggingsys
from shared.tools.retry_on_exception import retry_on_exception

logger = loggingsys.get_logger(__name__)

WS = "REGISTRATION"


class ApiService:
    def __init__(self):
        self.session = requests.Session()
        config = configuration.get_config()
        self.PROGRAM_ENDPOINT = (
            f"{config.DER_GATEWAY_URL}/registration-service/api/v2/registration/ws/{WS}/programs"
        )
        self.ENROLLMENT_ENDPOINT = (
            f"{config.DER_GATEWAY_URL}/registration-service/api/v2/registration/ws/{WS}/enrollment"
        )
        self.PROVISION_ENDPOINT = (
            f"{config.DER_GATEWAY_URL}/registration-service/api/v2/provision/programs"
        )

    def post_program(self, data: str):
        """Takes in the data as an XML string and posts it to the program endpoint.
        Will retry up to 3 times if the request fails with a short exponential backoff.
        """
        self._post(self.PROGRAM_ENDPOINT, data)

    def post_enrollment(self, data: str):
        """Takes in the data as an XML string and posts it to the enrollment endpoint.
        Will retry up to 3 times if the request fails with a short exponential backoff.
        """
        self._post(self.ENROLLMENT_ENDPOINT, data)

    def post_provision_program(self, data: str):
        """Takes in the data as an XML string and posts it to the enrollment endpoint.
        Will retry up to 3 times if the request fails with a short exponential backoff.
        """
        self._post(self.ENROLLMENT_ENDPOINT, data)

    @retry_on_exception(num_retries=3, backoff=1, errors=(HTTPError, RequestException))
    def _post(self, url: str, data: str) -> requests.Response:
        logger.info(f"Sending data to {url}. Data: {data}")
        headers = {"Content-Type": "application/xml"}
        response = self.session.post(url, data=data, headers=headers)
        logger.info(
            f"Response from {url}. Status code: {response.status_code}. Content: {response.content}"
        )
        response.raise_for_status()
        return response
