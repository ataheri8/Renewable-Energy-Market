import marshmallow as ma
from marshmallow import ValidationError, fields, validate, validates_schema

from pm.modules.progmgmt.enums import (
    AvailabilityType,
    DispatchTypeEnum,
    DOECalculationFrequency,
    DOELimitType,
    EnergyUnit,
    NotificationType,
    OrderType,
    ProgramOrderBy,
    ProgramStatus,
    ProgramTimePeriod,
    ScheduleTimeperiod,
)
from pm.restapi.validators import PaginatedRequestSchema
from shared.enums import (
    ControlOptionsEnum,
    DOEControlType,
    ProgramPriority,
    ProgramTypeEnum,
)
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class GeneralFieldsSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=1, max=75), required=True)
    program_type = fields.Enum(ProgramTypeEnum, required=True)
    start_date = fields.DateTime(format="iso")
    end_date = fields.DateTime(format="iso")
    program_priority = fields.Enum(ProgramPriority)
    availability_type = fields.Enum(AvailabilityType)
    check_der_eligibility = fields.Boolean()
    status = fields.Enum(ProgramStatus)
    define_contractual_target_capacity = fields.Boolean()
    notification_type = fields.Enum(NotificationType)

    @validates_schema
    def validate_start_end_times(self, data, **kwargs):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and end <= start:
            logger.error("start_date must be greater than end_date")
            raise ValidationError(
                "start_date must be greater than end_date", field_name="start_hour"
            )


class AvailableOperatingMonthsSchema(ma.Schema):
    jan = fields.Boolean(required=True)
    feb = fields.Boolean(required=True)
    mar = fields.Boolean(required=True)
    apr = fields.Boolean(required=True)
    may = fields.Boolean(required=True)
    jun = fields.Boolean(required=True)
    jul = fields.Boolean(required=True)
    aug = fields.Boolean(required=True)
    sep = fields.Boolean(required=True)
    oct = fields.Boolean(required=True)
    nov = fields.Boolean(required=True)
    dec = fields.Boolean(required=True)


class MinMaxSchema(ma.Schema):
    min = fields.Integer(required=False, allow_none=True)
    max = fields.Integer(required=False, allow_none=True)


class CumulativeEventDurationSchema(ma.Schema):
    DAY = fields.Nested(MinMaxSchema, required=False)
    WEEK = fields.Nested(MinMaxSchema, required=False)
    MONTH = fields.Nested(MinMaxSchema, required=False)
    YEAR = fields.Nested(MinMaxSchema, required=False)
    PROGRAM_DURATION = fields.Nested(MinMaxSchema, required=False)


class MaxNumberOfEventsPerTimePeriodSchema(ma.Schema):
    DAY = fields.Integer(required=False)
    WEEK = fields.Integer(required=False)
    MONTH = fields.Integer(required=False)
    YEAR = fields.Integer(required=False)
    PROGRAM_DURATION = fields.Integer(required=False)


class DispatchConstraintsSchema(ma.Schema):
    event_duration_constraint = fields.Nested(MinMaxSchema)
    cumulative_event_duration = fields.Nested(CumulativeEventDurationSchema)
    max_number_of_events_per_timeperiod = fields.Nested(MaxNumberOfEventsPerTimePeriodSchema)


class DemandManagementDispatchConstraintsSchema(ma.Schema):
    max_total_energy_per_timeperiod = fields.Float()
    max_total_energy_unit = fields.Enum(EnergyUnit)
    timeperiod = fields.Enum(ProgramTimePeriod)


class ResourceEligibilityCriteria(ma.Schema):
    max_real_power_rating = fields.Float()
    min_real_power_rating = fields.Float()


class DispatchOptOutSchema(ma.Schema):
    timeperiod = fields.Enum(ProgramTimePeriod, by_value=False, required=True)
    value = fields.Integer(validate=validate.Range(min=1), required=True)


class DispatchNotificationSchema(ma.Schema):
    text = fields.String(validate=validate.Length(min=1))
    lead_time = fields.Integer(validate=validate.OneOf([10, 30, 60, 360, 1440]), required=True)


class ServiceWindowSchema(ma.Schema):
    start_hour = fields.Integer(validate=validate.Range(min=0, max=23), required=True)
    end_hour = fields.Integer(validate=validate.Range(min=1, max=24), required=True)
    mon = fields.Boolean(required=True)
    tue = fields.Boolean(required=True)
    wed = fields.Boolean(required=True)
    thu = fields.Boolean(required=True)
    fri = fields.Boolean(required=True)
    sat = fields.Boolean(required=True)
    sun = fields.Boolean(required=True)

    @validates_schema
    def validate_start_end_times(self, data, **kwargs):
        start = data["start_hour"]
        end = data["end_hour"]
        if end <= start:
            logger.error("start_hour must be greater than end_hour")
            raise ValidationError(
                "start_hour must be greater than end_hour", field_name="start_hour"
            )


class HolidayExclusion(ma.Schema):
    holiday_name = fields.String(required=True)
    holiday_date = fields.Date(required=True)


class DynamicOperatingEnvelopeFields(ma.Schema):
    limit_type = fields.Enum(DOELimitType)
    calculation_frequency = fields.Enum(DOECalculationFrequency)
    control_type = fields.List(fields.Enum(DOEControlType))
    schedule_time_horizon_timeperiod = fields.Enum(ScheduleTimeperiod)
    schedule_time_horizon_number = fields.Integer(validate=validate.Range(min=0))
    schedule_timestep_mins = fields.Integer(validate=validate.Range(min=0))


class CreateUpdateProgramSchema(ma.Schema):
    general_fields = fields.Nested(GeneralFieldsSchema, required=True)
    dispatch_constraints = fields.Nested(DispatchConstraintsSchema)
    resource_eligibility_criteria = fields.Nested(ResourceEligibilityCriteria)
    avail_operating_months = fields.Nested(AvailableOperatingMonthsSchema)
    dispatch_max_opt_outs = fields.Nested(DispatchOptOutSchema, many=True)
    dispatch_notifications = fields.Nested(DispatchNotificationSchema, many=True)
    avail_service_windows = fields.Nested(ServiceWindowSchema, many=True)
    dynamic_operating_envelope_fields = fields.Nested(DynamicOperatingEnvelopeFields)
    demand_management_constraints = fields.Nested(DemandManagementDispatchConstraintsSchema)
    control_options = fields.List(fields.Enum(ControlOptionsEnum, required=False))
    dispatch_type = fields.Enum(DispatchTypeEnum, required=False)
    track_event = fields.Boolean(required=False)


class GeneralFieldsUpdateSchema(GeneralFieldsSchema):
    name = fields.String(validate=validate.Length(min=1, max=75))
    program_type = fields.Enum(ProgramTypeEnum)


class UpdateProgramSchema(CreateUpdateProgramSchema):
    general_fields = fields.Nested(GeneralFieldsUpdateSchema, required=False)


class ProgramQueryArgsSchema(PaginatedRequestSchema):
    order_by = fields.Enum(ProgramOrderBy, by_value=False, required=False)
    order_type = fields.Enum(OrderType, by_value=False, required=False)
    status = fields.Enum(ProgramStatus, by_value=False, required=False)
    program_type = fields.Enum(ProgramTypeEnum, by_value=False, required=False)
    start_date = fields.DateTime(format="iso", required=False)
    end_date = fields.DateTime(format="iso", required=False)


class HolidayExclusionsFileSchema(ma.Schema):
    calendars = ma.fields.Raw(type="file")


class CalendarEventsSchema(ma.Schema):
    startDate = fields.String(required=True)
    endDate = fields.String(required=True)
    name = fields.String(required=True)
    category = fields.String(required=False)
    substitutionDate = fields.String(required=False)


class CalendarInfoSchema(ma.Schema):
    mrid = fields.String(required=True)
    timezone = fields.String(required=True)
    year = fields.Integer(required=True)
    events = fields.List(fields.Nested(CalendarEventsSchema(), required=True))


class CalendarSchema(ma.Schema):
    calendars = fields.List(fields.Nested(CalendarInfoSchema(), required=True))
