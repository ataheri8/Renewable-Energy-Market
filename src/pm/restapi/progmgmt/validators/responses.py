import marshmallow as ma
from marshmallow import fields, validate

from pm.modules.progmgmt.enums import ProgramStatus
from pm.restapi.progmgmt.validators.requests import (
    AvailabilityType,
    AvailableOperatingMonthsSchema,
    DemandManagementDispatchConstraintsSchema,
    DispatchConstraintsSchema,
    DispatchNotificationSchema,
    DispatchOptOutSchema,
    DispatchTypeEnum,
    DOECalculationFrequency,
    DOELimitType,
    DynamicOperatingEnvelopeFields,
    NotificationType,
    ResourceEligibilityCriteria,
    ScheduleTimeperiod,
    ServiceWindowSchema,
)
from pm.restapi.validators import PaginatedResponseSchema
from shared.enums import (
    ControlOptionsEnum,
    DOEControlType,
    ProgramPriority,
    ProgramTypeEnum,
)


class HolidayCalendarEventsDict(ma.Schema):
    startDate = fields.String()
    endDate = fields.String()
    name = fields.String()
    category = fields.String(required=False)
    substitutionDate = fields.String(required=False)


class HolidayCalendarInfoDict(ma.Schema):
    mrid = fields.String()
    timezone = fields.String()
    year = fields.Integer()
    events = fields.Nested(HolidayCalendarEventsDict)


class ProgramSchema(ma.Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    program_type = fields.Enum(ProgramTypeEnum, by_value=False, required=True)
    program_priority = fields.Enum(ProgramPriority)
    start_date = fields.DateTime(format="iso")
    end_date = fields.DateTime(format="iso")


class ProgramFullSchema(ProgramSchema):
    limit_type = fields.Enum(DOELimitType, required=False)
    control_type = fields.List(fields.Enum(DOEControlType), required=False)
    status = fields.Enum(ProgramStatus, required=False)
    define_contractual_target_capacity = fields.Boolean(required=False)
    check_der_eligibility = fields.Boolean(required=False)
    availability_type = fields.Enum(AvailabilityType, required=False)
    notification_type = fields.Enum(NotificationType, required=False)
    dispatch_constraints = fields.Nested(DispatchConstraintsSchema, required=False)
    resource_eligibility_criteria = fields.Nested(ResourceEligibilityCriteria, required=False)
    avail_operating_months = fields.Nested(AvailableOperatingMonthsSchema, required=False)
    dispatch_max_opt_outs = fields.Nested(DispatchOptOutSchema, many=True, required=False)
    dispatch_notifications = fields.Nested(DispatchNotificationSchema, many=True, required=False)
    avail_service_windows = fields.Nested(ServiceWindowSchema, many=True, required=False)
    dynamic_operating_envelope_fields = fields.Nested(
        DynamicOperatingEnvelopeFields, required=False
    )
    demand_management_constraints = fields.Nested(
        DemandManagementDispatchConstraintsSchema, required=False
    )
    schedule_timestep_mins = fields.Integer(validate=validate.Range(min=0), required=False)
    schedule_time_horizon_timeperiod = fields.Enum(ScheduleTimeperiod, required=False)
    schedule_time_horizon_number = fields.Integer(validate=validate.Range(min=0), required=False)
    schedule_timestep_mins = fields.Integer(validate=validate.Range(min=0), required=False)
    calculation_frequency = fields.Enum(DOECalculationFrequency, required=False)
    control_options = fields.List(fields.Enum(ControlOptionsEnum), required=False)
    dispatch_type = fields.Enum(DispatchTypeEnum, required=False)
    track_event = fields.Boolean(required=False)
    holiday_exclusions = fields.Nested(HolidayCalendarEventsDict, required=False)


class ProgramListSchema(ma.Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    program_type = fields.Enum(ProgramTypeEnum, by_value=False, required=True)
    status = fields.Enum(ProgramStatus, by_value=False, required=True)
    start_date = fields.DateTime(format="iso", required=True)
    end_date = fields.DateTime(format="iso", required=True)
    created_at = fields.DateTime(format="iso", required=True)


class PaginatedProgramsListSchema(PaginatedResponseSchema):
    results = fields.Nested(ProgramListSchema, many=True)
