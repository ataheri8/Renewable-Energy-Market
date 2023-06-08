import json

import pytest

from pm.modules.enrollment.services.enrollment import EnrollmentRequestGenericFieldsDict
from pm.tests.tasks_test.task_tests import fake_enrollment_data_factory


def _dict_to_bytes(data: dict | list) -> bytes:
    return bytes(json.dumps(data), "utf-8")


@pytest.fixture
def der_control_payload_bytes():
    """Example payload from DER Gateway's der-control topic"""
    return _dict_to_bytes(
        {
            "dermControlId": "1",
            "dermDispatchId": "1",
            "controlId": "B94E28E2C65547B3B1F9C096D4F8952B",
            "controlGroupId": "1",
            "initiallyParticipatingDERs": ["9101080001", "9101080002"],
            "creationTime": 1635458197,
            "dermUserId": "John Doe",
            "startTime": 1635489900,
            "endTime": 1635497100,
            "controlType": "kW % Rated Capacity",
            "controlSetpoint": "77.77",
            "controlEventStatus": "scheduled",
        }
    )


@pytest.fixture
def der_response_payload_bytes():
    """Example payload from DER Gateway's der-response topic"""
    return _dict_to_bytes(
        {
            "controlId": "583F3555E5FE42E3B76A12E204935241",
            "edevId": "9101080002",
            "status": 11,
            "time": 1635489753,
        }
    )


@pytest.fixture
def fake_enrollment_data() -> EnrollmentRequestGenericFieldsDict:
    return fake_enrollment_data_factory()
