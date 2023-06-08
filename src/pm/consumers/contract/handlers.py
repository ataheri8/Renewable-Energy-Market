from typing import Optional, Type

from pm.modules.enrollment.contract_repository import ContractRepository
from pm.topics import ContractMessage, DerGatewayProgramMessage
from shared.repository import UOW
from shared.system.loggingsys import get_logger
from shared.tasks.decorators import register_topic_handler
from shared.validators.der_gateway_data import Contract, Enrollment, Program

logger = get_logger(__name__)

DEFAULT_HEADER_OP = "CREATED"


@register_topic_handler(ContractMessage.TOPIC, ContractMessage.schema())
def handle_contract(
    data: ContractMessage,
    headers: Optional[dict] = None,
    Repository: Type[ContractRepository] = ContractRepository,
):
    """Handles the contract topic and sends contract data to the der gateway program topic."""
    logger.info(f"Handling data for contract: {data}")
    with UOW() as uow:
        contract_repository = Repository(uow.session)
        enrollment_req = contract_repository.get_enrollment_and_program_by_contract_id(data.id)
    if not enrollment_req:
        raise ValueError(f"Enrollment not found for contract id {data.id}")
    program = Program.from_dict(enrollment_req.program.to_dict())  # type: ignore
    contract = Contract.from_dict(data.to_dict())
    enrollment = Enrollment.from_dict(enrollment_req.to_dict())  # type: ignore
    der_gateway_program_msg = DerGatewayProgramMessage(
        program=program, contract=contract, enrollment=enrollment
    )
    if headers:
        der_gateway_program_msg.headers["operation"] = headers.get("operation", DEFAULT_HEADER_OP)
    der_gateway_program_msg.send_to_kafka()
