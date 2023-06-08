import logging

from pm.data_transfer_objects.csv_upload_kafka_messages import EnrollmentRequestMessage
from pm.modules.enrollment.controller import EnrollmentController
from pm.modules.enrollment.models import *  # noqa
from pm.modules.enrollment.services.enrollment import (
    CreateUpdateEnrollmentRequestDict,
    EnrollmentRequestGenericFieldsDict,
)
from pm.modules.progmgmt.models import *  # noqa
from pm.modules.serviceprovider.models import *  # noqa
from pm.restapi.enrollment.validators.requests import GeneralFieldsEnrollmentSchema
from shared.minio_manager import Message
from shared.system.configuration import Config
from shared.tasks.decorators import register_topic_handler

ERROR_TOPIC = "error"
SUCCESS_TOPIC = "success"
logger = logging.getLogger(__name__)


@register_topic_handler(Config.CSV_INGESTION_TOPIC, schema=GeneralFieldsEnrollmentSchema(many=True))
def handle_enrollment_create_control(
    data: list[EnrollmentRequestGenericFieldsDict], headers: dict | None = None
):
    """given an enrollment, validate it & insert it into the database"""
    for datum in data:
        enrollment_dict: CreateUpdateEnrollmentRequestDict = CreateUpdateEnrollmentRequestDict(
            **{"general_fields": datum}  # type: ignore
        )
        EnrollmentController().create_enrollment_requests([enrollment_dict])


@register_topic_handler(
    EnrollmentRequestMessage.Meta.topic, schema=EnrollmentRequestMessage.schema(many=True)
)
def handle_enrollment_request_message(data: list[Message], headers: dict | None = None):
    EnrollmentRequestMessage.process_messages(list_of_messages=data)
