import marshmallow as ma
from marshmallow import fields

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType


class AvailableDersResponse(ma.Schema):
    der_id = fields.String(required=True)
    name = fields.String()
    nameplate_rating_unit = fields.Enum(LimitUnitType)
    nameplate_rating = fields.Float()
    der_type = fields.Enum(DerAssetType)
    resource_category = fields.Enum(DerResourceCategory)
    service_provider_id = fields.Integer()


class DersNoSPResponse(ma.Schema):
    der_id = fields.String(required=True)
    name = fields.String()
    nameplate_rating_unit = fields.Enum(LimitUnitType)
    nameplate_rating = fields.Float()
    der_type = fields.Enum(DerAssetType)
    resource_category = fields.Enum(DerResourceCategory)


class DerShortSchema(ma.Schema):
    der_id = fields.String(required=True)
