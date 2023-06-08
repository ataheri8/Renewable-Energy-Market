import types
import typing
from collections import defaultdict
from dataclasses import MISSING, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Sequence, Type, is_typeddict


class AsyncApiSchemaBuilder:
    METADATA_DESCRIPTION = "description"
    METADATA_EXAMPLE = "example"

    def _add_metadata(self, field_metadata, field_info) -> dict:
        description = field_metadata.get(self.METADATA_DESCRIPTION)
        example = field_metadata.get(self.METADATA_EXAMPLE)
        if description:
            field_info[self.METADATA_DESCRIPTION] = description
        if example:
            field_info[self.METADATA_EXAMPLE] = example
        return field_info

    def _is_optional(self, t: Any) -> bool:
        # Optional type is actually a Union type with the 2nd arg as None
        return typing.get_origin(t) is typing.Union and type(None) in typing.get_args(t)

    def _make_object(self, properties: dict, required: list[str]) -> dict:
        data = {"type": "object", "properties": properties}
        if required:
            required.sort()
            data["required"] = required
        return data

    def _get_type(self, f_type: Any) -> Any:
        if not hasattr(f_type, "__forward_arg__"):
            return f_type
        # because __future__ annotations replaces type hints with the ForwardRef type,
        # we need to get the real type if the module has included annotations
        return eval(f_type.__forward_arg__)

    def _get_field_data(self, f_type: Any) -> dict:
        f_type = self._get_type(f_type)
        field_info: dict = {}
        if f_type is str:
            field_info = {"type": "string"}
        elif f_type is int:
            field_info = {"type": "integer"}
        elif f_type in [float, complex, Decimal]:
            field_info = {"type": "number"}
        elif type(f_type) is type(Enum):
            field_info = {"type": "string", "enum": [e.name for e in f_type]}
        elif f_type in [datetime, date]:
            field_info = {"type": "string", "format": "datetime"}
        elif f_type is bool:
            field_info = {"type": "boolean"}
        elif f_type is list:
            field_info = {"type": "array"}
        elif self._is_optional(f_type):
            field_info = self._get_field_data(f_type.__args__[0])
        elif type(f_type) is types.GenericAlias and f_type.__origin__ is list:
            field_info = {"type": "array", "items": self._get_field_data(f_type.__args__[0])}
        elif (
            type(f_type) is types.GenericAlias
            and not is_typeddict(f_type)
            and f_type.__origin__ is dict
        ):
            field_info = {"type": "object"}
        elif type(f_type) is types.UnionType:  # noqa: E721
            field_info = {"oneOf": [self._get_field_data(a) for a in f_type.__args__]}
        elif is_dataclass(f_type):
            field_info = self.get_data(f_type)  # type: ignore
        elif hasattr(f_type, "__annotations__"):
            properties = {}
            required = []
            for k, v in f_type.__annotations__.items():
                if not self._is_optional(v):
                    required.append(k)
                properties[k] = self._get_field_data(v)
            field_info = self._make_object(properties, required)
        return field_info

    def get_data(self, schema: Type) -> dict:
        properties = {}
        required = []
        for field in fields(schema):
            if field.default is MISSING and not self._is_optional(field.type):
                required.append(field.name)
            properties[field.name] = self._get_field_data(field.type)
            if field.metadata:
                self._add_metadata(field.metadata, properties[field.name])
        return self._make_object(properties, required)

    @classmethod
    def build(cls, schema: Type) -> dict:
        """Builds an AsyncApi schema from a marshmallow schema"""
        return cls().get_data(schema)


def generate_asyncapi_spec(
    topic_list: Sequence[Type],
    title: str = "Kafka API",
    version: str = "0.0.1",
) -> dict:
    """Generates the AsyncAPI spec in JSON"""
    DOC_TYPE = "publish"
    schemas: dict = defaultdict(dict)
    topic_names: dict = defaultdict(list)
    channels: dict = defaultdict(dict)
    for t in topic_list:
        topic = get_topic(t)
        if topic in topic_names[topic]:
            raise ValueError(f"Topic name {topic} already exists. Did you register it twice?")
        topic_names[topic].append(DOC_TYPE)
        schemas[t.__name__] = AsyncApiSchemaBuilder.build(t)
        channels[topic][DOC_TYPE] = {
            "message": {"payload": {"$ref": f"#/components/schemas/{t.__name__}"}}
        }
    return {
        "asyncapi": "2.5.0",
        "info": {"title": title, "version": version},
        "channels": dict(channels),
        "components": {"schemas": dict(schemas)},
    }


def get_topic(t):
    try:
        return t.TOPIC
    except AttributeError:
        return t.Meta.topic
    except Exception:
        raise ValueError(f"Topic name for  {t.__name__}: error")
