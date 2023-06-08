import marshmallow as ma
from marshmallow import fields

from pm.modules.reports.enums import ReportTypeEnum
from pm.restapi.reports.validators.report_requests_validators import (
    ContractConstraintSummarySchema,
)
from pm.restapi.validators import PaginatedResponseSchema


class ReportSchema(ma.Schema):
    created_at = fields.DateTime(format="iso", required=True)
    updated_at = fields.DateTime(format="iso", required=True)
    report_type = fields.Enum(ReportTypeEnum, by_value=False, required=True)
    program_id = fields.Integer(required=True, default=None)
    service_provider_id = fields.Integer(required=True, default=None)
    start_report_date = fields.DateTime(format="iso", required=True)
    end_report_date = fields.DateTime(format="iso", required=True)
    created_by = fields.String(required=True)
    report_details = fields.String(required=True)
    user_id = fields.Integer(required=True)
    total_events = fields.Integer(required=True)
    average_event_duration = fields.Float(required=True)
    dispatched_der = fields.Integer(required=True)
    total_der_in_program = fields.Integer(required=True)
    avail_flexibility_up = fields.Float(required=True)
    avail_flexibility_down = fields.Float(required=True)
    constraint_violations = fields.Integer(required=True)
    constraint_warnings = fields.Integer(required=True)


class EventListSchema(ma.Schema):
    id = fields.Integer(required=True)
    report_id = fields.Integer(required=True)
    event_start = fields.DateTime(format="iso", required=True)  # type: ignore
    event_end = fields.DateTime(format="iso", required=True)
    number_of_dispatched_der = fields.Integer(required=True)
    number_of_opted_out_der = fields.Integer(required=True)
    requested_capacity = fields.Float(required=True)
    dispatched_capacity = fields.Float(required=True)
    event_status = fields.String(required=True)


class PaginatedEventsListSchema(PaginatedResponseSchema):
    results = fields.Nested(EventListSchema, many=True)


class ContractDetailsListSchema(ma.Schema):
    id = fields.Integer(required=True)
    enrollment_date = fields.DateTime(format="iso", required=True)
    report_id = fields.Integer(required=True)
    der_id = fields.String(required=True)
    service_provider_id = fields.Integer(required=True)
    contract_constraint_id = fields.Integer(required=True)
    contract_constraints = fields.Nested(ContractConstraintSummarySchema)


class PaginatedContractDetailsListSchema(PaginatedResponseSchema):
    results = fields.Nested(ContractDetailsListSchema, many=True)


class ReportListSchema(ReportSchema):
    results = fields.Nested(ReportSchema, many=True)
