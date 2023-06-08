from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, TypedDict

from shared.tasks.producer import MessageData
from shared.tools.asyncapi import AsyncApiSchemaBuilder, generate_asyncapi_spec


class FakeEnum(Enum):
    property1 = "property1"
    property2 = "property2"


@dataclass
class ExampleNestedClass:
    test_1: str
    test_2: int


class TypedDictExample(TypedDict):
    int_example: int
    nested_example: ExampleNestedClass


@dataclass
class ExampleMessageData(MessageData):
    TOPIC = "der-warehouse.der"

    int_example: int = field(metadata={"example": "stuff", "description": "hello"})
    float_example: float
    str_example: str
    list_example: list[str] = field(
        metadata={"example": '["hi"]', "description": "An example of a list"}
    )
    datetime_example: datetime
    dict_example: dict[str, int]
    boolean_example: bool
    enum_example: FakeEnum
    nested_example: ExampleNestedClass
    nested_many_example: list[ExampleNestedClass]
    union_example: str | int
    optional_example: Optional[str]
    typed_dict_example: TypedDictExample = None


def test_async_api():
    schemas = {ExampleMessageData.__name__: AsyncApiSchemaBuilder.build(ExampleMessageData)}
    expected = {
        "ExampleMessageData": {
            "type": "object",
            "properties": {
                "int_example": {"type": "integer", "description": "hello", "example": "stuff"},
                "float_example": {"type": "number"},
                "str_example": {"type": "string"},
                "list_example": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "An example of a list",
                    "example": '["hi"]',
                },
                "datetime_example": {"type": "string", "format": "datetime"},
                "dict_example": {"type": "object"},
                "boolean_example": {"type": "boolean"},
                "enum_example": {"type": "string", "enum": ["property1", "property2"]},
                "nested_example": {
                    "type": "object",
                    "properties": {"test_1": {"type": "string"}, "test_2": {"type": "integer"}},
                    "required": ["test_1", "test_2"],
                },
                "nested_many_example": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"test_1": {"type": "string"}, "test_2": {"type": "integer"}},
                        "required": ["test_1", "test_2"],
                    },
                },
                "union_example": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                "optional_example": {"type": "string"},
                "typed_dict_example": {
                    "type": "object",
                    "properties": {
                        "int_example": {"type": "integer"},
                        "nested_example": {
                            "type": "object",
                            "properties": {
                                "test_1": {"type": "string"},
                                "test_2": {"type": "integer"},
                            },
                            "required": ["test_1", "test_2"],
                        },
                    },
                    "required": ["int_example", "nested_example"],
                },
            },
            "required": [
                "boolean_example",
                "datetime_example",
                "dict_example",
                "enum_example",
                "float_example",
                "int_example",
                "list_example",
                "nested_example",
                "nested_many_example",
                "str_example",
                "union_example",
            ],
        }
    }
    assert schemas == expected


class TestGenerateAsyncAPI:
    def test_generate_asyncapi_spec(self):
        @dataclass
        class Schema1(MessageData):
            TOPIC = "topic1"

            field1: str

        @dataclass
        class Schema2(MessageData):
            TOPIC = "topic2"

            field2: int

        s1 = Schema1(field1="test")
        assert s1.TOPIC == "topic1"
        topic_list = [Schema1, Schema2]
        asyncapi_spec = generate_asyncapi_spec(topic_list)
        assert asyncapi_spec == {
            "asyncapi": "2.5.0",
            "channels": {
                "topic1": {
                    "publish": {"message": {"payload": {"$ref": "#/components/schemas/Schema1"}}}
                },
                "topic2": {
                    "publish": {"message": {"payload": {"$ref": "#/components/schemas/Schema2"}}}
                },
            },
            "components": {
                "schemas": {
                    "Schema1": {
                        "type": "object",
                        "properties": {"field1": {"type": "string"}},
                        "required": ["field1"],
                    },
                    "Schema2": {
                        "type": "object",
                        "properties": {"field2": {"type": "integer"}},
                        "required": ["field2"],
                    },
                }
            },
            "info": {"title": "Kafka API", "version": "0.0.1"},
        }
