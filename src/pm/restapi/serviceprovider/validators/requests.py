import marshmallow as ma
import phonenumbers
from marshmallow import ValidationError, fields, pre_load, validate, validates
from phonenumbers.phonenumberutil import NumberParseException

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.restapi.utils import string_to_none
from shared.system import loggingsys

logger = loggingsys.get_logger(__name__)


class GeneralFieldsServiceProviderSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=1, max=75), required=True)
    service_provider_type = fields.Enum(ServiceProviderType, required=True)
    status = fields.Enum(ServiceProviderStatus, required=True)


class PrimaryContactSchema(ma.Schema):
    email_address = fields.Email(required=True)
    phone_number = fields.String(required=True)

    @validates("phone_number")
    def validate_phonenumber(self, phone_number):
        phone_number = phone_number.strip()
        if not phone_number:
            logger.error("Phone number is not valid")
            raise ValidationError("Phone number is not valid", field_name="phone_number")
        if not phone_number.startswith("+"):
            phone_number = "+1" + phone_number
        try:
            phone_number = phonenumbers.parse(phone_number)
        except NumberParseException as e:
            logger.error(e._msg + phone_number + " could not be parsed")
            raise ValidationError("Phone number is not valid", field_name="phone_number")
        if not phonenumbers.is_valid_number(phone_number):
            logger.error("Phone number is not valid")
            raise ValidationError("Phone number is not valid", field_name="phone_number")


class NotificationContactSchema(ma.Schema):
    email_address = fields.Email(required=False, allow_none=True)
    phone_number = fields.String(required=False, allow_none=True)

    @pre_load(pass_many=False)
    def _string_to_none(self, data, many, **kwargs):
        return string_to_none(data)

    @validates("phone_number")
    def validate_phonenumber(self, phone_number):
        if not phone_number:
            return
        phone_number = phone_number.strip()
        if not phone_number.startswith("+"):
            phone_number = "+1" + phone_number
        try:
            phone_number = phonenumbers.parse(phone_number)
        except NumberParseException as e:
            logger.error(e._msg + phone_number + " could not be parsed")
            raise ValidationError("Phone number is not valid", field_name="phone_number")
        if not phonenumbers.is_valid_number(phone_number):
            logger.error("Phone number is not valid")
            raise ValidationError("Phone number is not valid", field_name="phone_number")


class AddressSchema(ma.Schema):
    street = fields.String(required=False)
    city = fields.String(required=False)
    state = fields.String(required=False)
    country = fields.String(required=False)
    zip_code = fields.String(required=False)
    apt_unit = fields.String(required=False)


class CreateUpdateServiceProviderSchema(ma.Schema):
    general_fields = fields.Nested(GeneralFieldsServiceProviderSchema, required=True)
    primary_contact = fields.Nested(PrimaryContactSchema, required=True)
    notification_contact = fields.Nested(NotificationContactSchema, required=False)
    address = fields.Nested(AddressSchema, required=False)


class ServiceProviderDerAssociationUpload(ma.Schema):
    file = fields.Field(metadata={"type": "string", "format": "byte"}, required=True)


class DerIdSchema(ma.Schema):
    der_id = fields.String(required=True)


class AssociatedDersSchema(DerIdSchema):
    id = fields.Integer(required=True)
    name = fields.String()
    nameplate_rating_unit = fields.Enum(LimitUnitType)
    nameplate_rating = fields.Integer()
    der_type = fields.Enum(DerAssetType)
    resource_category = fields.Enum(DerResourceCategory)


class ServiceProviderUploadSchema(ma.Schema):
    file = fields.Raw(metadata={"type": "string", "format": "byte"}, required=True)
