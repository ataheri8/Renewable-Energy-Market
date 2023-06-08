import json

import pendulum
import pytest


def _dict_to_bytes(data: dict) -> bytes:
    return bytes(json.dumps(data), "utf-8")


@pytest.fixture
def der_payload_bytes():
    """Example payload from DER Warehouse der topic"""
    der_topic_payload = {
        "id": 1,
        "der_id": "1234-someId-5678",
        "name": "myder",
        "der_type": "WIND_FARM",
        "resource_category": "GENERIC",
        "nameplate_rating": 50,
        "nameplate_rating_unit": "kW",
        "is_deleted": False,
        "extra": {"somedata": "hi"},
        "created_at": str(pendulum.now()),
        "updated_at": str(pendulum.now()),
    }
    return _dict_to_bytes(der_topic_payload)
