from __future__ import annotations

from datetime import datetime

from pm.modules.event_tracking.builders.der_dispatch_dicts import (
    BuildDerDispatchDicts,
    CreateDerDispatchDict,
)
from pm.modules.event_tracking.models.der_response import CreateDerResponseDict
from pm.modules.event_tracking.repository import EventRepository
from shared.repository import UOW
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class ReportUOW(UOW):
    def __enter__(self):
        super().__enter__()
        self.repository = EventRepository(self.session)
        return self


class EventController:
    def __init__(self):
        self.unit_of_work = ReportUOW()

    def create_der_dispatch(self, data: list[CreateDerDispatchDict]):
        """Creates a der dispatch in response to an event on DER Gateway."""
        with self.unit_of_work as uow:
            id_set = set(d["contract_id"] for d in data)
            contract_ids = uow.repository.filter_contract_id_set(id_set)
            if not contract_ids:
                logger.info(
                    f"No contract has contract IDs {id_set}. Dispatches will not be created"
                )
                return
            dispatches = BuildDerDispatchDicts.build(contract_ids, data)
            logger.info(f"Inserting {len(dispatches)} der dispatches")
            uow.repository.bulk_insert_der_dispatches(dispatches)
            uow.commit()
            logger.info(f"Committed {len(dispatches)} der dispatches")

    def create_der_response(self, data: CreateDerResponseDict):
        """Creates a der response."""
        with self.unit_of_work as uow:
            logger.info(f"Inserting {len(data)} der responses")
            uow.repository.bulk_insert_der_responses(data)
            uow.commit()
            logger.info(f"Committed {len(data)} der responses")

    def calculate_contract_constraints(self, day: datetime):
        """Create and save a summary of the constraints"""
        with self.unit_of_work as uow:
            for contract in uow.repository.get_all_active_contracts():
                summary = uow.repository.calculate_contract_constraints(
                    day, contract.id, contract.program
                )
                uow.repository.save(summary)
                uow.commit()

    def get_processed_constraints(self, contract_id: int) -> dict:
        """Get the processed constraints from ContractConstraintSummary model.
        Returns a processed constraints.
        """
        with self.unit_of_work as uow:
            constraints_summary = uow.repository.get_constraints_summary_by_contract_id(contract_id)
            if constraints_summary:
                return constraints_summary.processed_summary_dict

            return {}
