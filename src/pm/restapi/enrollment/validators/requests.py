import marshmallow as ma
from marshmallow import fields, pre_load

from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.restapi.utils import string_to_none
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class GeneralFieldsEnrollmentSchema(ma.Schema):
    program_id = fields.Integer(required=True)
    service_provider_id = fields.Integer(required=True)
    der_id = fields.String(required=True)


class DynamicOperatingEnvelopesSchema(ma.Schema):
    default_limits_active_power_import_kw = fields.Float(required=False, allow_none=True)
    default_limits_active_power_export_kw = fields.Float(required=False, allow_none=True)
    default_limits_reactive_power_import_kw = fields.Float(required=False, allow_none=True)
    default_limits_reactive_power_export_kw = fields.Float(required=False, allow_none=True)

    @pre_load(pass_many=False)
    def _string_to_none(self, data, many, **kwargs):
        return string_to_none(data)


class DemandResponseSchema(ma.Schema):
    import_target_capacity = fields.Float(required=False, allow_none=True)
    export_target_capacity = fields.Float(required=False, allow_none=True)

    @pre_load(pass_many=False)
    def _string_to_none(self, data, many, **kwargs):
        return string_to_none(data)


class CreateUpdateEnrollmentSchema(ma.Schema):
    general_fields = fields.Nested(GeneralFieldsEnrollmentSchema, required=True)
    dynamic_operating_envelopes = fields.Nested(DynamicOperatingEnvelopesSchema, required=False)
    demand_response = fields.Nested(DemandResponseSchema, required=False)


class UpdateContractSchema(ma.Schema):
    contract_type = fields.Enum(ContractType, required=True)
    enrollment_request_id = fields.Integer(required=True)
    contract_status = fields.Enum(ContractStatus, required=True)
    der_id = fields.String(required=True)
    program_id = fields.Integer(required=True)
    service_provider_id = fields.Integer(required=True)
    dynamic_operating_envelopes = fields.Nested(DynamicOperatingEnvelopesSchema, required=False)
    demand_response = fields.Nested(DemandResponseSchema, required=False)


class EnrollmentRequestsUploadSchema(ma.Schema):
    file = fields.Field(metadata={"type": "string", "format": "byte"}, required=True)
