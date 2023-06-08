import json

import requests  # type: ignore

from shared.system import configuration, loggingsys

logger = loggingsys.get_logger(__name__)


class AuditLoggingAdapter:
    def __init__(self):
        config = configuration.get_config()
        self.session = requests.Session()
        self.POST_LOG_ENDPOINT = f"{config.ALS_URL}/api/create"
        self.GET_LOG_ENDPOINT = f"{config.ALS_URL}/api/read"

    def read_log(self):
        # TODO: Fix ALS read method first and then implement this
        raise NotImplementedError

    def write_log(self, actor: str, action: str, **kwargs) -> requests.Response:
        audit_log = dict(action=action, actor=actor, **kwargs)
        resp = self._post(self.POST_LOG_ENDPOINT, audit_log)
        return resp

    def _post(self, url: str, data: dict) -> requests.Response:
        logger.info(f"Sending data to {url}. Data: {data}")
        payload = json.dumps(data)
        headers = {"Content-Type": "application/json"}
        response = self.session.post(url, data=payload, headers=headers)
        logger.info(
            f"Response from {url}. Status code: {response.status_code}. Content: {response.content}"
        )
        response.raise_for_status()
        return response
