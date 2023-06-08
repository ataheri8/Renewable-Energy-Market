import logging
from http import HTTPStatus

from flask import request, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from minio.error import S3Error, ServerError

from pm.data_transfer_objects.csv_upload_kafka_messages import EnrollmentRequestMessage
from pm.modules.enrollment.controller import EnrollmentController
from pm.modules.enrollment.repository import EnrollmentNotFound
from pm.modules.progmgmt.repository import ProgramNotFound
from pm.restapi.enrollment.validators.requests import (
    CreateUpdateEnrollmentSchema,
    EnrollmentRequestsUploadSchema,
)
from pm.restapi.enrollment.validators.responses import (
    EnrollmentCRUDResponse,
    EnrollmentSchema,
)
from pm.restapi.exceptions import raise_custom_error, raise_error
from pm.restapi.utils import send_csv_template
from pm.restapi.validators import ErrorSchema
from shared.exceptions import LoggedError

logger = logging.getLogger(__name__)
blueprint = Blueprint(
    "Enrollment API",
    __name__,
    description="Endpoints for Enrollment API",
    url_prefix="/api/enrollment",
)


class EnrollmentError(ErrorSchema):
    """We must name the error schema or Flask Smorest will name it and generate a warning"""


@blueprint.route("/")
class EnrollmentCore(MethodView):
    @blueprint.arguments(CreateUpdateEnrollmentSchema(many=True))
    @blueprint.response(HTTPStatus.CREATED, EnrollmentCRUDResponse(many=True))
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=EnrollmentError)
    def post(self, enrollment):
        """Create a new Enrollment"""
        enrollment_request_ids = EnrollmentController().create_enrollment_requests(enrollment)
        return enrollment_request_ids

    @blueprint.response(HTTPStatus.OK, EnrollmentSchema(many=True))
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=EnrollmentError)
    def get(self):
        """Get all Enrollments"""
        return EnrollmentController().get_all_enrollment_requests()


@blueprint.route("/<int:id>")
class EnrollmentOne(MethodView):
    @blueprint.response(HTTPStatus.OK, EnrollmentSchema(many=False))
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=EnrollmentError)
    def get(self, id):
        """Get a single Enrollment"""
        try:
            return EnrollmentController().get_enrollment_request(id)
        except EnrollmentNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<program_id>/upload")
class EnrollmentRequestsBulkUpload(MethodView):
    @blueprint.arguments(
        EnrollmentRequestsUploadSchema,
        location="files",
    )
    @blueprint.response(HTTPStatus.ACCEPTED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=EnrollmentError)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=EnrollmentError)
    @blueprint.alt_response(HTTPStatus.INTERNAL_SERVER_ERROR, schema=EnrollmentError)
    def post(self, files, program_id: int):
        """Upload a list of DER's to enroll them into a program"""
        session_id = request.form.get(
            "session_id",
            "84:No session id provided",
        )
        try:
            payload = files["file"]
            EnrollmentController().enrollment_request_upload(
                program_id=program_id,
                file=payload,
                tags={"session_id": session_id},
            )
        except ProgramNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)
        except (ServerError, S3Error) as e:
            raise_custom_error(HTTPStatus.INTERNAL_SERVER_ERROR, code=e.code, message=e.message)
        except LoggedError as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)


@blueprint.route("/report/program/<int:program_id>")
class EnrollmentReport(MethodView):
    @blueprint.response(
        HTTPStatus.OK,
        {"format": "csv", "type": "string"},
        content_type="text/csv",
    )
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=EnrollmentError)
    def get(self, program_id):
        """Get Enrollment Report for a particular Program"""
        try:
            report = EnrollmentController().get_enrollment_report(program_id)
            return send_file(
                report,
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"enrollment_report_program_{program_id}.csv",
            )
        except ProgramNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/download_template")
class EnrollmentTemplateDownload(MethodView):
    @blueprint.response(
        HTTPStatus.OK,
        {"format": "csv", "type": "string"},
        content_type="text/csv",
    )
    def get(self):
        return send_csv_template(EnrollmentRequestMessage)
