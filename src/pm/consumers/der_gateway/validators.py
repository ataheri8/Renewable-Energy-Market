from datetime import datetime, timezone

import marshmallow as ma


class TimeZoneMixin:
    def _convert_unix_to_datetime(self, ts: int) -> datetime:
        return datetime.fromtimestamp(ts, tz=timezone.utc)


class DerResponseSchema(ma.Schema, TimeZoneMixin):
    """Schema for the der-response topic.
    Converts the keys to snake case and to program manager terms
    """

    control_id = ma.fields.String(required=True, data_key="controlId")
    der_id = ma.fields.String(required=True, data_key="edevId")
    der_response_status = ma.fields.Integer(required=True, data_key="status")
    der_response_time = ma.fields.Integer(required=True, data_key="time")

    @ma.post_load
    def unix_to_datetime(self, data, **_):
        data["der_response_time"] = self._convert_unix_to_datetime(data["der_response_time"])
        return data
