import logging
from http import HTTPStatus

from flask.views import MethodView
from flask_smorest import Blueprint

from pm.modules.derinfo.controller import DerInfoController
from pm.restapi.derinfo.validators.responses import (
    AvailableDersResponse,
    DersNoSPResponse,
)

logger = logging.getLogger(__name__)
blueprint = Blueprint(
    "DER API",
    __name__,
    description="Endpoints for DER API",
    url_prefix="/api/der",
)


@blueprint.route("/available_ders")
class AvailableDers(MethodView):
    @blueprint.response(HTTPStatus.OK, AvailableDersResponse(many=True))
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST)
    def get(self):
        """Get all DERs that are associated with a service provider and free to form a contract"""
        return DerInfoController().get_ders_with_service_provider_but_no_contract()


@blueprint.route("/non_associated_ders")
class DerAssociation(MethodView):
    @blueprint.response(HTTPStatus.OK, DersNoSPResponse(many=True))
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST)
    def get(self):
        """Get all DERs without a Service Provider"""
        return DerInfoController().get_ders_with_no_service_provider()
