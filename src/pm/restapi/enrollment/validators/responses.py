import marshmallow as ma
from marshmallow import fields

from pm.modules.enrollment.enums import (
    ContractStatus,
    ContractType,
    EnrollmentCRUDStatus,
    EnrollmentRejectionReason,
    EnrollmentRequestStatus,
)
from pm.restapi.derinfo.validators.responses import DerShortSchema
from pm.restapi.enrollment.validators.requests import (
    DemandResponseSchema,
    DynamicOperatingEnvelopesSchema,
)
from pm.restapi.progmgmt.validators.responses import ProgramSchema
from pm.restapi.serviceprovider.validators.responses import ServiceProviderShortSchema


class EnrollmentSchema(ma.Schema):
    id = fields.Integer(required=True)
    program_id = fields.Integer(required=True)
    service_provider_id = fields.Integer(required=True)
    rejection_reason = fields.Enum(EnrollmentRejectionReason, required=False)
    der_id = fields.String(required=True)
    enrollment_status = fields.Enum(EnrollmentRequestStatus, required=True)
    dynamic_operating_envelopes = fields.Nested(DynamicOperatingEnvelopesSchema, required=True)
    demand_response = fields.Nested(DemandResponseSchema, required=False)


class EnrollmentCRUDResponse(ma.Schema):
    id = fields.String(required=False)
    status = fields.Enum(EnrollmentCRUDStatus, required=True)
    message = fields.String(required=False)
    data = fields.Dict(required=False)


class ContractSchema(ma.Schema):
    id = fields.Integer(required=True)
    contract_status = fields.Enum(ContractStatus, required=True)
    contract_type = fields.Enum(ContractType, required=True)
    enrollment_request_id = fields.Integer(required=True)
    der_id = fields.String(required=True)
    program_id = fields.Integer(required=True)
    service_provider_id = fields.Integer(required=True)
    dynamic_operating_envelopes = fields.Nested(DynamicOperatingEnvelopesSchema, required=False)
    demand_response = fields.Nested(DemandResponseSchema, required=False)
    der = fields.Nested(DerShortSchema, required=True)
    program = fields.Nested(ProgramSchema, required=True)
    service_provider = fields.Nested(ServiceProviderShortSchema, required=True)


class NumberViolationSchema(ma.Schema):
    number = fields.Integer(required=True)
    violation = fields.Boolean(required=True)


class EventDurationSchema(ma.Schema):
    DAY = fields.Nested(NumberViolationSchema, required=False)
    WEEK = fields.Nested(NumberViolationSchema, required=False)
    MONTH = fields.Nested(NumberViolationSchema, required=False)
    YEAR = fields.Nested(NumberViolationSchema, required=False)
    PROGRAM_DURATION = fields.Nested(NumberViolationSchema, required=False)


class ProcessedConstraintsSchema(ma.Schema):
    cumulative_event_duration = fields.Nested(EventDurationSchema, required=False)
    max_number_of_events_per_timeperiod = fields.Nested(EventDurationSchema, required=False)
    max_total_energy_per_timeperiod = fields.Nested(EventDurationSchema, required=False)
    opt_outs = fields.Nested(EventDurationSchema, required=False)
