import logging
from typing import Type

from flask import Response, send_file

from pm.modules.serviceprovider.controller import ServiceProviderController
from shared.minio_manager import Message

logger = logging.getLogger(__name__)


def send_csv_template(message_class: Type[Message]) -> Response:
    template = message_class.generate_csv_template()
    logger.info(f"Downloading {template.name} as CSV template")
    return send_file(
        template,
        as_attachment=True,
        mimetype="text/csv",
        download_name=template.name,
    )


def send_service_provider_csv(service_provider_id: int):
    file = ServiceProviderController().download_service_provider_data(service_provider_id)
    logger.info(f"Downloading csv data for {service_provider_id}")
    return send_file(file, as_attachment=True, mimetype="text/csv", download_name=file.name)


# https://stackoverflow.com/questions/60491613/allowing-empty-dates-with-marshmallow
def string_to_none(data):
    turn_to_none = lambda x: None if x == "" else x  # noqa: E731
    for k, v in data.items():
        data[k] = turn_to_none(v)
    return data
