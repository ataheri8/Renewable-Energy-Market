from datetime import datetime, timezone

from pm.consumers.der_gateway.validators import DerResponseSchema


class TestValidators:
    def test_der_response_schema(self, der_response_payload_bytes):
        got = DerResponseSchema().loads(der_response_payload_bytes)
        # should output dict in snake case
        expected = {
            "control_id": "583F3555E5FE42E3B76A12E204935241",
            "der_id": "9101080002",
            "der_response_status": 11,
            "der_response_time": datetime.fromtimestamp(1635489753, tz=timezone.utc),
        }

        assert got == expected
