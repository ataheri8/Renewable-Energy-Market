import logging
from http import HTTPStatus

from flask.views import MethodView
from flask_smorest import Blueprint

from pm.modules.reports.controller import (
    InvalidReportArgs,
    InvalidReportDates,
    ReportController,
)
from pm.modules.reports.repository import ReportNotFound
from pm.modules.reports.services.report import CreateReport
from pm.restapi.exceptions import raise_error
from pm.restapi.reports.validators.report_requests_validators import (
    CreateReportSchema,
    ReportQueryArgsSchema,
)
from pm.restapi.reports.validators.report_response_validators import (
    PaginatedContractDetailsListSchema,
    PaginatedEventsListSchema,
    ReportListSchema,
    ReportSchema,
)
from pm.restapi.validators import ErrorSchema

logger = logging.getLogger(__name__)

blueprint = Blueprint(
    "Reports API", __name__, description="Endpoints for Reports API", url_prefix="/api/reports"
)


class ReportError(ErrorSchema):
    """We must name the error schema or Flask Smorest will name it and generate a warning"""


@blueprint.route("/")
class ReportCore(MethodView):
    @blueprint.arguments(CreateReportSchema)
    @blueprint.response(HTTPStatus.CREATED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ReportError)
    def post(self, report):
        """Create a new Report"""
        try:
            data = CreateReport.from_dict(report)
            ReportController().create_report(data)
        except (InvalidReportArgs, InvalidReportDates) as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.response(HTTPStatus.OK, ReportListSchema)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ReportError)
    def get(self):
        """Get report list"""
        return ReportController().get_all_reports()


@blueprint.route("/<int:report_id>/summary")
class ReportCoreByID(MethodView):
    @blueprint.response(HTTPStatus.OK, ReportSchema)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ReportNotFound)
    def get(self, report_id: int):
        """Get a Report by report_id"""
        try:
            return ReportController().get_report(report_id)
        except ReportNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<int:report_id>/events")
class ReportEventDetails(MethodView):
    @blueprint.arguments(ReportQueryArgsSchema, location="query")
    @blueprint.response(HTTPStatus.OK, PaginatedEventsListSchema)
    def get(self, query):
        """Get's paginated list of events from a report"""
        try:
            return ReportController().get_event_report_details(query)
        except ReportNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<int:report_id>/contracts")
class ReportContractDetails(MethodView):
    @blueprint.arguments(ReportQueryArgsSchema, location="query")
    @blueprint.response(HTTPStatus.OK, PaginatedContractDetailsListSchema)
    def get(self, query):
        """Get's paginated list of contract details from a report"""
        try:
            return ReportController().get_contract_report_details(query)
        except ReportNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
