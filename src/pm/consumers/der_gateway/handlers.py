import pendulum

from pm.modules.event_tracking.controller import EventController
from pm.modules.event_tracking.models.der_response import OPT_OUT_STATUS_CODE
from shared.system.loggingsys import get_logger
from shared.tasks.consumer import ConsumerMessage
from shared.tasks.decorators import ConsumerType, register_topic_handler

logger = get_logger(__name__)

DER_CONTROL_TOPIC = "der-control"
DER_RESPONSE_TOPIC = "der-response"


@register_topic_handler(DER_CONTROL_TOPIC, consumer_type=ConsumerType.BATCH)
def handle_der_control(data: list[ConsumerMessage]):
    logger.info(f"Handling der control: Message number: {len(data)}")
    filtered_data = []
    for message in data:
        try:
            new_data = {
                "event_id": message.value["dermDispatchId"],
                "start_date_time": int(message.value["startTime"]),
                "end_date_time": int(message.value["endTime"]),
                "event_status": message.value["controlEventStatus"],
                "control_command": message.value["controlSetpoint"],
                "control_type": message.value["controlType"],
                "contract_id": int(message.value["controlGroupId"]),
                "control_id": message.value["controlId"],
            }
            filtered_data.append(new_data)
        except (KeyError, ValueError) as e:
            logger.warning(f"DER Dispatch data error: {e}")
            continue
    logger.info(f"Filtered data: {len(filtered_data)}")
    EventController().create_der_dispatch(filtered_data)  # type: ignore


@register_topic_handler(DER_RESPONSE_TOPIC, consumer_type=ConsumerType.BATCH)
def handle_der_response(data: list[ConsumerMessage]):
    logger.info(f"Handling der response: Message number: {len(data)}")
    filtered_data = []
    for message in data:
        try:
            status = int(message.value["status"])
            new_data = {
                "control_id": message.value["controlId"],
                "der_id": message.value["edevId"],
                "der_response_status": status,
                "der_response_time": pendulum.from_timestamp(message.value["time"]),
                "is_opt_out": status == OPT_OUT_STATUS_CODE,
            }
            filtered_data.append(new_data)
        except (KeyError, ValueError) as e:
            logger.warning(f"DER Response data error: {e}")
            continue
    EventController().create_der_response(filtered_data)  # type: ignore
