from http import HTTPStatus

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from minio.error import S3Error, ServerError
from werkzeug.datastructures import FileStorage

from pm.data_transfer_objects.csv_upload_kafka_messages import (
    ServiceProviderDERAssociateMessage,
    ServiceProviderMessage,
)
from pm.modules.serviceprovider.controller import (
    InvalidServiceProviderArgs,
    ServiceProviderController,
)
from pm.modules.serviceprovider.repository import (
    ServiceProviderDerAssociationNotFound,
    ServiceProviderNoDerAssociationFound,
    ServiceProviderNotFound,
)
from pm.modules.serviceprovider.services.service_provider import (
    CreateUpdateServiceProvider,
    ServiceProviderNameDuplicate,
)
from pm.restapi.exceptions import raise_custom_error, raise_error
from pm.restapi.serviceprovider.validators.requests import (
    CreateUpdateServiceProviderSchema,
    DerIdSchema,
    ServiceProviderDerAssociationUpload,
    ServiceProviderUploadSchema,
)
from pm.restapi.serviceprovider.validators.responses import ServiceProviderSchema
from pm.restapi.utils import send_csv_template, send_service_provider_csv
from pm.restapi.validators import ErrorSchema
from shared.exceptions import LoggedError
from shared.system import loggingsys

logger = loggingsys.get_logger(__name__)
blueprint = Blueprint(
    "ServiceProvider API",
    __name__,
    description="Endpoints for ServiceProvider API",
    url_prefix="/api/serviceprovider",
)


class ServiceProviderError(ErrorSchema):
    """We must name the error schema or Flask Smorest will name it and generate a warning"""


@blueprint.route("/")
class ServiceProviderCore(MethodView):
    @blueprint.arguments(CreateUpdateServiceProviderSchema)
    @blueprint.response(HTTPStatus.CREATED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ServiceProviderError)
    def post(self, service_provider_dict):
        """Create a new ServiceProvider"""
        try:
            data = CreateUpdateServiceProvider.from_dict(service_provider_dict)
            id = ServiceProviderController().create_service_provider(data)
        except (InvalidServiceProviderArgs, ServiceProviderNameDuplicate) as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)
        return {"Created Service provider with id": id}

    @blueprint.response(HTTPStatus.OK, ServiceProviderSchema(many=True))
    def get(self):
        """Get all Service Providers"""
        return ServiceProviderController().get_all_serviceproviders()


@blueprint.route("/<int:id>")
class ServiceProviderOne(MethodView):
    @blueprint.response(HTTPStatus.OK, ServiceProviderSchema(many=False))
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ServiceProviderError)
    def get(self, id):
        """Get a single Service Provider"""
        try:
            return ServiceProviderController().get_serviceprovider(id)
        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)

    @blueprint.arguments(CreateUpdateServiceProviderSchema)
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ServiceProviderError)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ServiceProviderError)
    def patch(self, service_provider_dict, id):
        """Update a ServiceProvider"""
        try:
            data = CreateUpdateServiceProvider.from_dict(service_provider_dict)
            id = ServiceProviderController().update_service_provider(id, data)
            return {"Updated Service provider with id": id}
        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)

        except (
            InvalidServiceProviderArgs,
            ServiceProviderNameDuplicate,
        ) as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)

    @blueprint.response(HTTPStatus.NO_CONTENT)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ServiceProviderError)
    def delete(self, id):
        """Delete a single Service Provider"""
        try:
            ServiceProviderController().delete_service_provider(id)
        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<int:id>/enable")
class ServiceProviderEnable(MethodView):
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ServiceProviderError)
    def patch(self, id):
        """Enable a Service Provider"""
        try:
            id = ServiceProviderController().enable_service_provider(id)
            return {"Enabled Service provider with id": id}

        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<int:id>/disable")
class ServiceProviderDisable(MethodView):
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ServiceProviderError)
    def patch(self, id):
        """Disable a Service Provider"""
        try:
            id = ServiceProviderController().disable_service_provider(id)
            return {"Disabled Service provider with id": id}
        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/upload")
class ServiceProviderUpload(MethodView):
    @blueprint.arguments(ServiceProviderUploadSchema, location="files")
    @blueprint.response(HTTPStatus.ACCEPTED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ServiceProviderError)
    @blueprint.alt_response(HTTPStatus.INTERNAL_SERVER_ERROR, schema=ServiceProviderError)
    def post(self, files):
        """Create a multiple ServiceProvider from a CSV file"""
        logger.info("Uploading Service Provider CSV")
        try:
            session_id = request.form.get(
                "session_id",
                "114:No session id provided",
            )
            payload: FileStorage = files["file"]
            ServiceProviderController().service_providers_file_upload(
                payload,
                tags={"session_id": session_id},
            )
        except (ServerError, S3Error) as e:
            raise_custom_error(HTTPStatus.INTERNAL_SERVER_ERROR, code=e.code, message=e.message)
        except LoggedError as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)


@blueprint.route("/download_service_provider_template")
class ServiceProviderTemplateDownload(MethodView):
    @blueprint.response(
        HTTPStatus.OK,
        {"format": "csv", "type": "string"},
        content_type="text/csv",
    )
    def get(self):
        return send_csv_template(ServiceProviderMessage)


@blueprint.route("/<service_provider_id>/upload")
class ServiceProviderDerAssocUpload(MethodView):
    @blueprint.arguments(
        ServiceProviderDerAssociationUpload,
        location="files",
    )
    @blueprint.response(HTTPStatus.ACCEPTED)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ServiceProviderError)
    @blueprint.alt_response(HTTPStatus.NOT_FOUND, schema=ServiceProviderError)
    @blueprint.alt_response(HTTPStatus.INTERNAL_SERVER_ERROR, schema=ServiceProviderError)
    def post(self, files, service_provider_id: int):
        """Upload a list of DER's for a single Service Provider"""
        try:
            session_id = request.form.get(
                "session_id",
                "152:No session id provided",
            )
            payload = files["file"]
            ServiceProviderController().associate_ders_file_upload(
                service_provider_id=service_provider_id,
                file=payload,
                tags={"session_id": session_id},
            )

        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except (ServerError, S3Error) as e:
            raise_custom_error(HTTPStatus.INTERNAL_SERVER_ERROR, code=e.code, message=e.message)
        except LoggedError as e:
            raise_error(HTTPStatus.BAD_REQUEST, e)


@blueprint.route("/<service_provider_id>/<der_id>")
class ServiceProviderDerAssoc(MethodView):
    @blueprint.response(HTTPStatus.NO_CONTENT)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ServiceProviderError)
    def delete(self, service_provider_id: int, der_id: int):
        """Delete an association"""
        try:
            ServiceProviderController().delete_der_service_provider(service_provider_id, der_id)
        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
        except ServiceProviderDerAssociationNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/<service_provider_id>/associate_ders")
class ServiceProviderDersAssoc(MethodView):
    @blueprint.arguments(DerIdSchema(many=True))
    @blueprint.response(HTTPStatus.OK)
    @blueprint.alt_response(HTTPStatus.BAD_REQUEST, schema=ServiceProviderError)
    def post(self, der_list, service_provider_id):
        """Associate DERs with ServiceProvider"""
        try:
            ServiceProviderController().get_serviceprovider(service_provider_id)
            return ServiceProviderController().associate_ders(service_provider_id, der_list)
        except ServiceProviderNotFound as e:
            raise_error(HTTPStatus.NOT_FOUND, e)


@blueprint.route("/download_der_association_template")
class ServiceProviderDERAssocTemplateDownload(MethodView):
    @blueprint.response(
        HTTPStatus.OK,
        {"format": "csv", "type": "string"},
        content_type="text/csv",
    )
    def get(self):
        return send_csv_template(ServiceProviderDERAssociateMessage)


@blueprint.route("<service_provider_id>/download_data")
class ServiceProviderDataDownload(MethodView):
    @blueprint.response(
        HTTPStatus.OK,
        {"format": "csv", "type": "string"},
        content_type="text/csv",
    )
    def get(self, service_provider_id: int):
        try:
            return send_service_provider_csv(service_provider_id)
        except (ServiceProviderNotFound, ServiceProviderNoDerAssociationFound) as e:
            raise_error(HTTPStatus.NOT_FOUND, e)
