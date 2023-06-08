from http import HTTPStatus

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint  # type: ignore
from marshmallow import Schema, fields

from shared.system.loggingsys import get_logger

logger = get_logger(__name__)

blueprint = Blueprint("system", "system", description="System endpoints.")


class HealthCheckSchema(Schema):
    message = fields.String(required=True)


@blueprint.route("/health-check")
class HealthCheck(MethodView):
    @blueprint.response(HTTPStatus.OK, HealthCheckSchema)
    def get(self):
        return jsonify({"message": "online"}), HTTPStatus.OK
