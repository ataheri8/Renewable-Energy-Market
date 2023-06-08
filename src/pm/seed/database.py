# -----------------------------------------------
# Database Seeder

# Script to seed the database with some data for testing.
# -----------------------------------------------

import random
from uuid import uuid4

from dotenv import load_dotenv

from pm.config import PMConfig
from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.enums import ContractStatus, ContractType
from pm.modules.enrollment.models.enrollment import Contract
from pm.tests import factories
from shared.system import configuration, database, loggingsys


def _make_ders(der_ids: list[str]) -> list[DerInfo]:
    return [
        DerInfo(
            der_id=der_id,
            name=f"DER-{der_id}",
            der_type=random.choice(list(DerAssetType)),
            nameplate_rating=round(random.uniform(1, 100), 4),
            nameplate_rating_unit=LimitUnitType.kWh,
            resource_category=random.choice(list(DerResourceCategory)),
        )
        for der_id in der_ids
    ]


def _make_contract(enrollment_request_id: int, der_id: str, program_id: int, sp_id: int):
    return Contract(
        enrollment_request_id=enrollment_request_id,
        der_id=der_id,
        contract_status=ContractStatus.ACTIVE,
        contract_type=ContractType.ENROLLMENT_CONTRACT,
        program_id=program_id,
        service_provider_id=sp_id,
    )


def seed():
    load_dotenv()

    config = configuration.init_config(PMConfig)
    loggingsys.init(config)
    database.init(config)

    # make 1 of each type of program
    program = factories.GenericProgramFactory(id=1, name="Generic")
    factories.DemandManagementProgramFactory(id=2, name="Demand Management")
    factories.DynamicOperatingEnvelopesProgram(id=3, name="DOE")

    # make 2 service providers
    der_ids = [f"_{uuid4()}" for _ in range(10)]
    sp = factories.ServiceProviderFactory(id=1, ders=_make_ders(der_ids))
    factories.ServiceProviderFactory(id=2)

    # use the service provider 1's DERs to make enrollments and contracts
    contracted_der_id_1 = der_ids[0]
    contracted_der_id_2 = der_ids[1]
    factories.EnrollmentRequestFactory(
        id=1,
        service_provider=sp,
        program=program,
        der_id=contracted_der_id_1,
        contract=_make_contract(1, contracted_der_id_1, program.id, sp.id),
    )
    factories.EnrollmentRequestFactory(
        id=2,
        service_provider=sp,
        program=program,
        der_id=contracted_der_id_2,
        contract=_make_contract(1, contracted_der_id_2, program.id, sp.id),
    )


if __name__ == "__main__":
    seed()
