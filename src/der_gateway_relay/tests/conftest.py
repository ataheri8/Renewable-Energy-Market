import pytest

from der_gateway_relay.config import DerGatewayRelayConfig
from shared.system import configuration
from shared.validators import der_gateway_data as program_data


@pytest.fixture
def der_gateway_program_payload():
    """Example payload from PM der-gateway-program topic"""
    return {
        "program": {
            "id": 1,
            "name": "Test Program",
            "program_type": "DEMAND_MANAGEMENT",
            "start_date": "2021-01-01",
            "end_date": "2021-12-31",
            "program_priority": "P0",
            "control_type": [],
            "control_options": ["OP_MOD_VOLT_VAR", "OP_MOD_LVRT_MAY_TRIP"],
            "holiday_exclusions": {
                "calendars": [
                    {
                        "mrid": "mrid",
                        "timezone": "America/Los_Angeles",
                        "year": 2021,
                        "events": [
                            {
                                "startDate": "2021-01-01",
                                "endDate": "2021-01-01",
                                "name": "New Year's Day",
                                "category": "National Holiday",
                                "substitutionDate": "2021-01-01",
                            }
                        ],
                    }
                ]
            },
            "dispatch_constraints": {
                "event_duration_constraint": {
                    "min": 1,
                    "max": 60,
                },
                "cumulative_event_duration": {
                    "DAY": {
                        "min": 1,
                        "max": 60,
                    },
                    "WEEK": {
                        "min": 1,
                        "max": 60,
                    },
                    "MONTH": {
                        "min": 1,
                        "max": 60,
                    },
                    "YEAR": {
                        "min": 1,
                        "max": 60,
                    },
                    "PROGRAM_DURATION": {
                        "min": 1,
                        "max": 60,
                    },
                },
                "max_number_of_events_per_timeperiod": {
                    "DAY": 1,
                    "WEEK": 1,
                    "MONTH": 1,
                    "YEAR": 1,
                    "PROGRAM_DURATION": 1,
                },
            },
            "avail_service_windows": [
                {
                    "id": 1,
                    "start_hour": 0,
                    "end_hour": 23,
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                }
            ],
            "avail_operating_months": {
                "id": 1,
                "jan": True,
                "feb": True,
                "mar": True,
                "apr": True,
                "may": True,
                "jun": True,
                "jul": True,
                "aug": True,
                "sep": True,
                "oct": True,
                "nov": True,
                "dec": True,
            },
            "demand_management_constraints": {
                "max_total_energy_per_timeperiod": 1,
                "max_total_energy_unit": "kWh",
                "timeperiod": "DAY",
            },
        },
        "contract": {
            "id": 1,
            "contract_type": "demand_response",
        },
        "enrollment": {
            "der_id": "der_id",
        },
    }


@pytest.fixture
def single_payload(der_gateway_program_payload):
    return program_data.DerGatewayProgram.from_dict(der_gateway_program_payload)


@pytest.fixture
def config():
    config = DerGatewayRelayConfig()
    configuration.init_config(config)
    return config
