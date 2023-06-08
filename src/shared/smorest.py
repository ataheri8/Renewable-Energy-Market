from flask import Flask
from flask_smorest import Api
from marshmallow import fields


def _enum_to_properties(self, field: fields.Field, **_) -> dict:
    """Add an OpenAPI extension for fields.Enum instances.
    Produces the correct OpenAPI schema for Enum.

    https://apispec.readthedocs.io/en/latest/using_plugins.html#custom-fields
    """
    if isinstance(field, fields.Enum):
        return {"type": "string", "enum": [e.name for e in field.enum]}
    return {}


def api_factory(app: Flask, title: str, version: str) -> Api:
    """Creates a Flask-Smorest API instance with default configuration.
    Also adds a custom field converter to the marshmallow plugin to generate
    the correct OpenAPI schema for Enum fields.
    """
    app.config["API_TITLE"] = title
    app.config["API_VERSION"] = version
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["OPENAPI_URL_PREFIX"] = "/openapi"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    api = Api(app)
    # add custom field converter to marshmallow plugin
    api.ma_plugin.converter.add_attribute_function(_enum_to_properties)
    return api
