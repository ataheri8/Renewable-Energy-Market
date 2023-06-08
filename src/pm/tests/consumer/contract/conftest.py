import json

import pytest


def _dict_to_bytes(data: dict) -> bytes:
    return bytes(json.dumps(data), "utf-8")


@pytest.fixture
def contract_payload():
    """Example payload from Contract topic"""
    return {
        "id": 1,
        "created_at": "2023-03-27 20:01:41.338171+00:00",
        "updated_at": "2023-03-27 20:01:41.338171+00:00",
        "enrollment_request_id": 1,
        "program_id": 1,
        "service_provider_id": 1,
        "der_id": "_3a9189d6-ee06-49c5-b814-b495b62df192",
        "contract_status": "ACCEPTED",
        "contract_type": "ENROLLMENT_CONTRACT",
        "dynamic_operating_envelopes": None,
        "demand_response": None,
    }


@pytest.fixture
def contract_payload_bytes(contract_payload):
    """Example payload from Contract topic"""
    return _dict_to_bytes(contract_payload)
