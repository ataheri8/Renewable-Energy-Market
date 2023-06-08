from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.modules.serviceprovider.services.service_provider import (
    CreateUpdateServiceProvider,
    ServiceProviderService,
)


class TestServiceProviderService:
    def generate_args(self):
        service_provider_args = CreateUpdateServiceProvider.from_dict(
            dict(
                general_fields=dict(
                    name="test",
                    service_provider_type=ServiceProviderType.AGGREGATOR,
                    status=ServiceProviderStatus.ACTIVE,
                ),
                primary_contact=dict(
                    email_address="mlh@ge.com",
                    phone_number="905-444-5566",
                ),
                address=dict(
                    street="123 Which Street",
                    city="NoCity",
                    state="NoState",
                    country="NoCountry",
                    zip_code="A1B2C3",
                ),
            )
        )
        return service_provider_args

    def test_create_serviceprovider(self):
        service_provider_args = self.generate_args()
        sp_service = ServiceProviderService()
        service_provider = sp_service.create_service_provider(
            name=service_provider_args.general_fields.name,
            service_provider_type=service_provider_args.general_fields.service_provider_type,
            status=service_provider_args.general_fields.status,
            primary_contact=service_provider_args.primary_contact,
        )
        sp_service.set_service_provider_fields(service_provider, service_provider_args)
        assert service_provider.name == service_provider_args.general_fields.name
        assert isinstance(service_provider.primary_contact, dict)
        assert isinstance(service_provider.address, dict)

    def test_disable_serviceprovider(self):
        service_provider_args = self.generate_args()
        sp_service = ServiceProviderService()
        service_provider = sp_service.create_service_provider(
            name=service_provider_args.general_fields.name,
            service_provider_type=service_provider_args.general_fields.service_provider_type,
            status=service_provider_args.general_fields.status,
            primary_contact=service_provider_args.primary_contact,
        )
        sp_service.set_service_provider_fields(service_provider, service_provider_args)
        sp_service.disable_service_provider(service_provider)
        assert service_provider.status == ServiceProviderStatus.INACTIVE

    def test_enable_serviceprovider(self):
        service_provider_args = self.generate_args()
        sp_service = ServiceProviderService()
        service_provider = sp_service.create_service_provider(
            name=service_provider_args.general_fields.name,
            service_provider_type=service_provider_args.general_fields.service_provider_type,
            status=service_provider_args.general_fields.status,
            primary_contact=service_provider_args.primary_contact,
        )
        sp_service.set_service_provider_fields(service_provider, service_provider_args)
        sp_service.enable_service_provider(service_provider)
        assert service_provider.status == ServiceProviderStatus.ACTIVE

    def test_delete_serviceprovider(self):
        service_provider_args = self.generate_args()
        sp_service = ServiceProviderService()
        service_provider = sp_service.create_service_provider(
            name=service_provider_args.general_fields.name,
            service_provider_type=service_provider_args.general_fields.service_provider_type,
            status=service_provider_args.general_fields.status,
            primary_contact=service_provider_args.primary_contact,
        )
        sp_service.set_service_provider_fields(service_provider, service_provider_args)
        sp_service.delete_service_provider(service_provider)
        assert service_provider.status == ServiceProviderStatus.INACTIVE
        assert service_provider.deleted is True
