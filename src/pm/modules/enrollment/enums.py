import enum
from typing import Optional

from pm.modules.progmgmt.enums import ProgramStatus


class EnrollmentRequestStatus(enum.Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class ContractStatus(enum.Enum):
    ACCEPTED = "ACCEPTED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    USER_CANCELLED = "USER_CANCELLED"
    SYSTEM_CANCELLED = "SYSTEM_CANCELLED"

    @classmethod
    def is_system_cancelled(cls, status) -> bool:
        return status == cls.SYSTEM_CANCELLED

    @classmethod
    def is_user_cancelled(cls, status) -> bool:
        return status == cls.USER_CANCELLED

    @classmethod
    def is_expired(cls, status) -> bool:
        return status == cls.EXPIRED

    @classmethod
    def is_active_or_accepted(cls, status) -> bool:
        return status in {cls.ACTIVE, cls.ACCEPTED}

    @classmethod
    def map_program_status_to_contract_status(cls, program_status: Optional[ProgramStatus]):
        ret_dict = {
            ProgramStatus.DRAFT: ContractStatus.ACCEPTED,
            ProgramStatus.PUBLISHED: ContractStatus.ACCEPTED,
            ProgramStatus.ACTIVE: ContractStatus.ACTIVE,
            ProgramStatus.ARCHIVED: ContractStatus.EXPIRED,
        }
        return ret_dict.get(program_status, None)  # type: ignore


class ContractKafkaOperation(enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    REACTIVATED = "REACTIVATED"


class EnrollmentRejectionReason(enum.Enum):
    DER_NOT_FOUND = "DER not found in DER Warehouse"
    ELIGIBILITY_DATA_NOT_FOUND = "DER eligibility data not found in the DER Warehouse"
    DER_DOES_NOT_MEET_CRITERIA = "DER does not meet the program criteria"
    DER_NOT_ASSOCIATED_WITH_SERVICE_PROVIDER = "DER is not associated with given Servicer Provider"

    def get_readable_text(self) -> str:
        return str(self.value)


class ContractType(enum.Enum):
    ENROLLMENT_CONTRACT = "ENROLLMENT_CONTRACT"


class EnrollmentCRUDStatus(enum.Enum):
    CREATED = "CREATED"
    NOT_CREATED = "NOT_CREATED"
    RETRIEVED = "RETRIEVED"
    UPDATED = "UPDATED"
    NOT_UPDATED = "NOT_UPDATED"
    DELETED = "DELETED"
    NOT_DELETED = "NOT_DELETED"
