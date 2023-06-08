from http import HTTPStatus

import pytest

from pm.modules.enrollment.contract_controller import ContractController
from pm.modules.enrollment.contract_repository import ContractRepository
from pm.modules.enrollment.enums import ContractStatus
from pm.modules.serviceprovider.controller import ServiceProviderController
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


class TestPM432(TestDataMixin):
    """
    https://opusonesolutions.atlassian.net/browse/PM-432
    When a service provider DER association is changed, delete DERs from contracts which
    are not associated with any service provider and system cancel the contract
    """

    @pytest.fixture
    def contract_setup(self, db_session):
        program = factories.ProgramFactory(id=1)
        service_provider = factories.ServiceProviderFactory()
        der = factories.DerFactory(der_id="der_1", service_provider_id=service_provider.id)
        enrollment_request = factories.EnrollmentRequestFactory(
            program=program,
            service_provider=service_provider,
            der=der,
        )
        contract = factories.ContractFactory(
            id=1,
            program=program,
            service_provider=service_provider,
            enrollment_request=enrollment_request,
            der=der,
        )
        return {"der": der, "contract": contract, "svc_provider": service_provider}

    def test_service_provider_der_association_deleted(self, db_session, client, contract_setup):
        """PM-1005
        Given there is a der associated with a service provider in the system
        And that DER is already enrolled in a contract
        When the user deletes the association between the ServiceProvider
        And DER by hiting /api/serviceprovider/<service_provider_id>/<der_id>
        Then check all contracts in the database
        And remove the DER from the contract
        And cancel the contract if no DER is associated with it
        """
        service_provider = contract_setup["svc_provider"]
        der = contract_setup["der"]
        contract = contract_setup["contract"]
        contract_id = contract.id
        resp = client.delete(f"api/serviceprovider/{service_provider.id}/{der.id}")
        new_contract = ContractController().get_contract(contract_id, eager_load=True)
        assert resp.status_code == HTTPStatus.NO_CONTENT
        assert new_contract.contract_status == ContractStatus.SYSTEM_CANCELLED

    def test_service_provider_der_reassociation(self, db_session, client, contract_setup):
        """PM-1011
        Given User wants to change the association of an enrolled der with a new service provider
        And the user first hits /api/serviceprovider/<old-service_provider_id>/<der_id>
        And deletes the association
        When the user hits /api/serviceprovider/<new-service_provider_id>/upload
        And includes the der in the upload file
        Then check all contracts in  the database
        And remove the DER from the contract
        And cancel the contract if no DER is associated with it
        """
        service_provider = contract_setup["svc_provider"]
        der_1 = contract_setup["der"]
        der_2 = factories.DerFactory(der_id="der_2")
        der_2_id = der_2.der_id
        contract = contract_setup["contract"]
        contract_id = contract.id
        resp = client.delete(f"api/serviceprovider/{service_provider.id}/{der_1.id}")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        der_object = dict(
            der_rdf_id=der_2_id,
        )
        ServiceProviderController().associate_ders(service_provider.id, [der_object])
        new_contract = ContractController().get_contract(contract_id, eager_load=True)
        assert new_contract.contract_status == ContractStatus.SYSTEM_CANCELLED

    def test_association_deleted_der_not_enrolled(self, db_session, client, contract_setup):
        """PM-1012
        Given there is a der associated with a service provider in the system
        And that DER is not enrolled in a contract
        When the user deletes the association between the ServiceProvider
        And DER by hiting /api/serviceprovider/<service_provider_id>/<der_id>
        Then check all contracts in the database
        And don't cancel any contract as DER is not enrolled in any contract
        """
        service_provider = contract_setup["svc_provider"]
        not_enrolled_der = factories.DerFactory(
            der_id="not_enrolled", service_provider_id=service_provider.id
        )
        not_enrolled_der_id = not_enrolled_der.der_id
        contract = contract_setup["contract"]
        contract_id = contract.id
        resp = client.delete(f"api/serviceprovider/{service_provider.id}/{not_enrolled_der.id}")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        new_contract = ContractController().get_contract(contract_id, eager_load=True)
        assert new_contract.contract_status != ContractStatus.SYSTEM_CANCELLED
        assert new_contract.der_id != not_enrolled_der_id

    def test_reassociation_der_not_enrolled(self, db_session, client, contract_setup):
        """PM-1015
        Given the DER is associated with a service provider
        And the DER is not enrolled in any program
        And User wants to change the association of a der with a new service provider
        And User first hits /api/serviceprovider/<old-service_provider_id>/<der_id>
        And deletes the association
        When User hits /api/serviceprovider/<new-service_provider_id>/upload
        And includes the der in the upload file
        Then check all contracts in  the database
        And don't cancel any contract as DER is not enrolled in any contract
        """

        service_provider = contract_setup["svc_provider"]
        not_enrolled_der1 = factories.DerFactory(
            der_id="not_enrolled_1", service_provider_id=service_provider.id
        )
        not_enrolled_der2 = factories.DerFactory(der_id="not_enrolled_2")

        not_enrolled_der2_id = not_enrolled_der2.der_id
        contract = contract_setup["contract"]
        contract_id = contract.id
        resp = client.delete(f"api/serviceprovider/{service_provider.id}/{not_enrolled_der1.id}")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        der_object = dict(
            der_rdf_id=not_enrolled_der2_id,
        )
        ServiceProviderController().associate_ders(service_provider.id, [der_object])
        new_contract = ContractController().get_contract(contract_id, eager_load=True)
        assert new_contract.contract_status != ContractStatus.SYSTEM_CANCELLED

    def test_delete_service_provider_der_enrolled(self, db_session, client, contract_setup):
        """PM-1018
        Given the DER is associated with the ServiceProvider
        And the DER is enrolled into a program
        When User hits /api/serviceprovider/<int:id>
        And deletes the Service Provider
        Then check all contracts in  the database
        And remove the DER from the contract
        And remove the association
        And remove the service provider
        And cancel the contract if no DER is associated with it
        """
        service_provider = contract_setup["svc_provider"]
        contract = contract_setup["contract"]
        contract_id = contract.id
        resp = client.delete(f"api/serviceprovider/{service_provider.id}")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        new_contract = ContractController().get_contract(contract_id, eager_load=True)
        assert new_contract.contract_status == ContractStatus.SYSTEM_CANCELLED

    def test_delete_service_provider_der_not_enrolled(self, db_session, client):
        """
        Given the DER is associated with the ServiceProvider
        And the DER is not enrolled in any program
        When User hits /api/serviceprovider/<int:id>
        And deletes the Service Provider
        Then check all contracts in the database
        And remove the association
        And remove the service provider
        And don't cancel any contract as DER is not enrolled in any contract
        """

        service_provider = factories.ServiceProviderFactory(id=1)
        not_enrolled_der = factories.DerFactory(
            der_id="not_enrolled_der", service_provider_id=service_provider.id
        )
        not_enrolled_der_id = not_enrolled_der.der_id
        resp = client.delete(f"api/serviceprovider/{service_provider.id}")
        assert resp.status_code == HTTPStatus.NO_CONTENT
        with db_session() as session:
            contracts = ContractRepository(session).get_unexpired_contracts_by_der_id(
                not_enrolled_der_id
            )
        assert len(contracts) == 0
