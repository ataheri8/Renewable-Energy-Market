import marshmallow as ma
from marshmallow import fields

from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.restapi.serviceprovider.validators.requests import (
    AddressSchema,
    AssociatedDersSchema,
    NotificationContactSchema,
    PrimaryContactSchema,
)


class ServiceProviderSchema(ma.Schema):
    id = fields.Int(required=True)
    uuid = fields.String(required=True)
    name = fields.String(required=True)
    service_provider_type = fields.Enum(ServiceProviderType, required=True)
    status = fields.Enum(ServiceProviderStatus, required=True)
    primary_contact = fields.Nested(PrimaryContactSchema, required=True)
    address = fields.Nested(AddressSchema, required=False)
    ders = fields.List(fields.Nested(AssociatedDersSchema), required=False)
    notification_contact = fields.Nested(NotificationContactSchema, required=False)


class ServiceProviderShortSchema(ma.Schema):
    name = fields.String(required=True)
