import logging
from http import HTTPStatus

from flask.views import MethodView
from flask_smorest import Blueprint

from pm.modules.enrollment.contract_controller import ContractController
from pm.modules.enrollment.contract_repository import ContractNotFound
from pm.modules.enrollment.services.contract import (
    InvalidContractArgs,
    InvalidProgramStatusForContract,
    InvalidUndoCancellation,
)
from pm.modules.event_tracking.controller import EventController
from pm.modules.progmgmt.repository import ProgramNotFound
from pm.restapi.enrollment.validators.requests import UpdateContractSchema
from pm.restapi.enrollment.validators.responses import (
    ContractSchema,
    ProcessedConstraintsSchema,
)
from pm.restapi.exceptions import raise_error
from pm.restapi.validators import ErrorSchema

logger = logging.getLogger(__name__)
blueprint = Blueprint(
    "Contract API",
    __name__,
    description="Endpoints for Contract API",
    url_prefix="/api/contract",
)


class ContractError(ErrorSchema):
    """We must name the error schema or Flask Smorest will name it and generate a warning"""


@blueprint.route("/")
class Contract(MethodView):
    @blueprint.response(HTTPStatus.OK, ContractSchema(many=True))
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ContractError)
    def get(self):
        """Get all Contract"""
        return ContractController().get_all_contracts()


@blueprint.route("/<int:id>")
class ContractOne(MethodView):
    @blueprint.response(HTTPStatus.OK, ContractSchema(many=False))
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ContractError)
    def get(self, id):
        """Get a single Contract"""
        try:
            return ContractController().get_contract(id)
        except ContractNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)

    @blueprint.arguments(UpdateContractSchema)
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ContractError)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ContractError)
    def patch(self, contract, id):
        """Update a Contract"""
        try:
            id = ContractController().update_contract(id, contract)
            return {"Updated contract with id": id}
        except ContractNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)
        except InvalidContractArgs as e:
            logger.error(e)
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.response(HTTPStatus.NO_CONTENT)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ContractError)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ContractError)
    def delete(self, id):
        """Cancel a single Contract"""
        try:
            deleted = ContractController().cancel_contract(id)
            if not deleted:
                e = "The contract can not be cancelled with id " + str(id)
                logger.error(e)
                raise_error(HTTPStatus.BAD_REQUEST, InvalidContractArgs(message=e))
        except ContractNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<int:id>/reactivate")
class ReActivateContract(MethodView):
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ContractError)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ContractError)
    def patch(self, id):
        """Re-Activate a Contract"""
        try:
            ContractController().undo_cancel_contract(id)
        except (
            ContractNotFound,
            ProgramNotFound,
        ) as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except (
            InvalidProgramStatusForContract,
            InvalidUndoCancellation,
        ) as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)


@blueprint.route("/<int:id>/constraints")
class ContractConstraints(MethodView):
    @blueprint.response(HTTPStatus.OK, schema=ProcessedConstraintsSchema(many=False))
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ContractError)
    def get(self, id):
        """Get a single Contract"""
        try:
            contract = ContractController().get_contract(id)
            return EventController().get_processed_constraints(contract.id)
        except ContractNotFound as e:
            logger.error(e)
            raise_error(HTTPStatus.NOT_FOUND, e)
