from datetime import datetime

import marshmallow as ma
from marshmallow import ValidationError, fields, validates_schema

from pm.modules.reports.enums import OrderType, ReportTypeEnum
from pm.restapi.validators import PaginatedRequestSchema
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class CreateReportSchema(ma.Schema):
    report_type = fields.Enum(ReportTypeEnum, required=True)
    program_id = fields.Integer(required=False, default=0)
    service_provider_id = fields.Integer(required=False, default=0)
    start_report_date = fields.DateTime(format="iso", required=True)
    end_report_date = fields.DateTime(format="iso", required=True)
    created_by = fields.Str(required=True)

    @validates_schema
    def validate_start_end_times(self, data, **kwargs):
        start = data["start_report_date"]
        end = data["end_report_date"]
        if end <= start:
            logger.error("start_date must be greater than end_date")
            raise ValidationError(
                "start_date must be greater than end_date", field_name="start_report_date"
            )
        if end > datetime.now():
            logger.error("end_date must be in the past")
            raise ValidationError("end_date must be in the past", field_name="end_report_date")

    @validates_schema
    def validate_program_or_service_provider(self, data, **kwargs):
        report_type = data["report_type"]

        if report_type == ReportTypeEnum.INDIVIDUAL_PROGRAM and "program_id" not in data:
            logger.error("report type expects a program id to be provided")
            raise ValidationError(
                "report type expects a program id to be provided", field_name="program_id"
            )
        elif (
            report_type == ReportTypeEnum.INDIVIDUAL_SERVICE_PROVIDER
            and "service_provider_id" not in data
        ):
            logger.error("report type expects a service provider id to be provided")
            raise ValidationError(
                "report type expects a service provider id to be provided",
                field_name="service_provider_id",
            )


class ReportQueryArgsSchema(PaginatedRequestSchema):
    order_type = fields.Enum(OrderType, by_value=False, required=False)
    start_date = fields.DateTime(format="iso", required=False)
    end_date = fields.DateTime(format="iso", required=False)


class ContractConstraintSummarySchema(ma.Schema):
    id = fields.Integer(required=True)
    contract_id = fields.Integer(required=True)
    day = fields.DateTime(format="iso", required=True)

    # cumulative event duration
    cumulative_event_duration_day = fields.Integer(required=True)
    cumulative_event_duration_day_warning = fields.Boolean(required=True)
    cumulative_event_duration_day_violation = fields.Boolean(required=True)
    cumulative_event_duration_week = fields.Integer(required=True)
    cumulative_event_duration_week_warning = fields.Boolean(required=True)
    cumulative_event_duration_week_violation = fields.Boolean(required=True)
    cumulative_event_duration_month = fields.Integer(required=True)
    cumulative_event_duration_month_warning = fields.Boolean(required=True)
    cumulative_event_duration_month_violation = fields.Boolean(required=True)
    cumulative_event_duration_year = fields.Integer(required=True)
    cumulative_event_duration_year_warning = fields.Boolean(required=True)
    cumulative_event_duration_year_violation = fields.Boolean(required=True)
    cumulative_event_duration_program_duration = fields.Integer(required=True)
    cumulative_event_duration_program_duration_warning = fields.Boolean(required=True)
    cumulative_event_duration_program_duration_violation = fields.Boolean(required=True)
    # max_number_of_events_per_timeperiod
    max_number_of_events_per_timeperiod_day = fields.Integer(required=True)
    max_number_of_events_per_timeperiod_day_warning = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_day_violation = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_week = fields.Integer(required=True)
    max_number_of_events_per_timeperiod_week_warning = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_week_violation = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_month = fields.Integer(required=True)
    max_number_of_events_per_timeperiod_month_warning = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_month_violation = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_year = fields.Integer(required=True)
    max_number_of_events_per_timeperiod_year_warning = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_year_violation = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_program_duration = fields.Integer(required=True)
    max_number_of_events_per_timeperiod_program_duration_warning = fields.Boolean(required=True)
    max_number_of_events_per_timeperiod_program_duration_violation = fields.Boolean(required=True)
    # opt_outs
    opt_outs_day = fields.Integer(required=True)
    opt_outs_day_warning = fields.Boolean(required=True)
    opt_outs_day_violation = fields.Boolean(required=True)
    opt_outs_week = fields.Integer(required=True)
    opt_outs_week_warning = fields.Boolean(required=True)
    opt_outs_week_violation = fields.Boolean(required=True)
    opt_outs_month = fields.Integer(required=True)
    opt_outs_month_warning = fields.Boolean(required=True)
    opt_outs_month_violation = fields.Boolean(required=True)
    opt_outs_year = fields.Integer(required=True)
    opt_outs_year_warning = fields.Boolean(required=True)
    opt_outs_year_violation = fields.Boolean(required=True)
    opt_outs_program_duration = fields.Integer(required=True)
    opt_outs_program_duration_warning = fields.Boolean(required=True)
    opt_outs_program_duration_violation = fields.Boolean(required=True)
    # max_total_energy
    max_total_energy_per_timeperiod_day = fields.Float(required=True)
    max_total_energy_per_timeperiod_day_warning = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_day_violation = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_week = fields.Float(required=True)
    max_total_energy_per_timeperiod_week_warning = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_week_violation = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_month = fields.Float(required=True)
    max_total_energy_per_timeperiod_month_warning = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_month_violation = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_year = fields.Float(required=True)
    max_total_energy_per_timeperiod_year_warning = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_year_violation = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_program_duration = fields.Float(required=True)
    max_total_energy_per_timeperiod_program_duration_warning = fields.Boolean(required=True)
    max_total_energy_per_timeperiod_program_duration_violation = fields.Boolean(required=True)
