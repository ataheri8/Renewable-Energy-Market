from marshmallow import EXCLUDE

from pm.modules.derinfo.controller import DerInfoController
from pm.modules.derinfo.repository import DerUpdate
from pm.modules.enrollment.contract_controller import ContractController
from shared.system.loggingsys import get_logger
from shared.tasks.decorators import register_topic_handler

logger = get_logger(__name__)

DER_WAREHOUSE_DER_TOPIC = "der_warehouse.der"


@register_topic_handler(DER_WAREHOUSE_DER_TOPIC, DerUpdate.schema(unknown=EXCLUDE))
def handle_derwh_der(data: DerUpdate, headers: dict | None = None):
    logger.info(f"Handling DER data: {data}")
    if data.is_deleted:
        ContractController().cancel_contracts_by_der_id(data.der_id)
    # Upsert into DerInfo table on PM side
    DerInfoController().upsert_der_from_kafka(data)
