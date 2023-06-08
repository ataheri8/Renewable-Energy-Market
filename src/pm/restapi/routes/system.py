from http import HTTPStatus

from flask import jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint  # type: ignore
from marshmallow import Schema, fields

from shared.system.loggingsys import get_logger

logger = get_logger(__name__)

blueprint = Blueprint("System", __name__, description="System endpoints.", url_prefix="/api/system")


class HealthCheckSchema(Schema):
    message = fields.String(required=True)


@blueprint.route("/health-check")
class HealthCheck(MethodView):
    @blueprint.response(HTTPStatus.OK, HealthCheckSchema)
    def get(self):
        return jsonify({"message": "online"}), HTTPStatus.OK


@blueprint.route("/debug/headers")
@blueprint.response(HTTPStatus.OK)
def debug_headers():
    return jsonify(dict(zip(request.headers.keys(), request.headers.values()))), HTTPStatus.OK
