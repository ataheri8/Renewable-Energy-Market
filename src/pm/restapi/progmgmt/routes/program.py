import logging
from http import HTTPStatus

from flask.views import MethodView
from flask_smorest import Blueprint

from pm.modules.derinfo.controller import DerInfoController
from pm.modules.progmgmt.controller import InvalidProgramArgs, ProgramController
from pm.modules.progmgmt.models.avail_service_window import (
    ServiceWindowOverlapViolation,
)
from pm.modules.progmgmt.models.dispatch_opt_out import OptOutTimeperiodUniqueViolation
from pm.modules.progmgmt.models.program import (
    CreateUpdateProgram,
    InvalidProgramStartEndTimes,
    InvalidProgramStatus,
    ProgramNameDuplicate,
    ProgramSaveViolation,
)
from pm.modules.progmgmt.repository import (
    ProgramArchived,
    ProgramNotDraft,
    ProgramNotFound,
)
from pm.restapi.derinfo.validators.responses import AvailableDersResponse
from pm.restapi.exceptions import raise_error
from pm.restapi.progmgmt.validators.requests import (
    CalendarSchema,
    CreateUpdateProgramSchema,
    ProgramQueryArgsSchema,
    UpdateProgramSchema,
)
from pm.restapi.progmgmt.validators.responses import (
    PaginatedProgramsListSchema,
    ProgramFullSchema,
)
from pm.restapi.validators import ErrorSchema, JSONFileSchema

logger = logging.getLogger(__name__)

blueprint = Blueprint(
    "Program API", __name__, description="Endpoints for Program API", url_prefix="/api/program"
)


class ProgramError(ErrorSchema):
    """We must name the error schema or Flask Smorest will name it and generate a warning"""


@blueprint.route("/")
class ProgramCore(MethodView):
    @blueprint.arguments(CreateUpdateProgramSchema)
    @blueprint.response(HTTPStatus.CREATED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ProgramError)
    def post(self, program):
        """Create a new program"""
        try:
            data = CreateUpdateProgram.from_dict(program)
            ProgramController().create_program(data)
        except (
            InvalidProgramArgs,
            InvalidProgramStartEndTimes,
            ServiceWindowOverlapViolation,
            OptOutTimeperiodUniqueViolation,
            ProgramNameDuplicate,
            InvalidProgramStatus,
            ProgramSaveViolation,
        ) as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.arguments(ProgramQueryArgsSchema, location="query")
    @blueprint.response(HTTPStatus.OK, PaginatedProgramsListSchema)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ProgramError)
    def get(self, query):
        """Get program list with ordering and filtering"""
        return ProgramController().get_program_list(query)


@blueprint.route("/<int:program_id>")
class ProgramCoreByID(MethodView):
    @blueprint.response(HTTPStatus.OK, ProgramFullSchema)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ProgramNotFound)
    def get(self, program_id: int):
        try:
            return ProgramController().get_program(program_id)
        except ProgramNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except ProgramArchived as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.arguments(UpdateProgramSchema)
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ProgramError)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ProgramError)
    def patch(self, program, program_id: int):
        """Save an existing program"""
        try:
            if not program.get("general_fields"):
                program["general_fields"] = {}
            data = CreateUpdateProgram.from_dict(program)
            ProgramController().save_program(program_id, data)
        except ProgramNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except (
            InvalidProgramArgs,
            InvalidProgramStartEndTimes,
            ServiceWindowOverlapViolation,
            OptOutTimeperiodUniqueViolation,
            ProgramNameDuplicate,
            ProgramSaveViolation,
            InvalidProgramStatus,
        ) as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.response(HTTPStatus.NO_CONTENT)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ProgramError)
    @blueprint.alt_response(HTTPStatus.FORBIDDEN, schema=ProgramError)
    def delete(self, program_id: int):
        """Delete an existing program.

        Programs can only be deleted if they are still in DRAFT status.
        If the program is in any other status, it can be archived instead.
        """
        try:
            ProgramController().delete_draft_program(program_id)
        except ProgramNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except ProgramNotDraft as e:
            raise_error(HTTPStatus.FORBIDDEN, e)


@blueprint.route("/<int:program_id>/holiday-exclusions")
class HolidayExclusions(MethodView):
    @blueprint.arguments(JSONFileSchema(schema=CalendarSchema()), location="files")
    @blueprint.response(HTTPStatus.CREATED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ProgramError)
    def post(self, files, program_id: int):
        """Create a new holiday calendar exclusion"""
        try:
            ProgramController().save_holiday_exclusion(program_id, files)
        except ProgramNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except InvalidProgramStatus as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ProgramError)
    def get(self, program_id: int):
        return ProgramController().get_holiday_exclusions(program_id)


@blueprint.route("<program_id>/archive")
class ArchiveProgramCore(MethodView):
    @blueprint.response(HTTPStatus.NO_CONTENT, schema=ProgramError)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ProgramError)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ProgramError)
    def patch(self, program_id: int):
        """Archive an existing program"""
        try:
            ProgramController().archive_program(program_id)
        except ProgramNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except InvalidProgramStatus as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)


@blueprint.route("/<int:program_id>/available_ders")
class ProgramCoreAvailableDers(MethodView):
    @blueprint.response(HTTPStatus.OK, AvailableDersResponse(many=True))
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST)
    def get(self, program_id: int):
        """Get all DERs that are associated with a service provider and free to form a contract"""
        return DerInfoController().get_available_ders_not_in_program(program_id)


@blueprint.route("/<int:program_id>/enrollments")
class ProgramCoreEnrollments(MethodView):
    @blueprint.response(HTTPStatus.OK, AvailableDersResponse(many=True))
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST)
    def get(self, program_id: int):
        """Get all DERs that are enrolled in a program"""
        return DerInfoController().get_ders_in_program_with_enrollment(program_id)
