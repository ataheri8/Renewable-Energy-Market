from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Type

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as ENUM
from sqlalchemy import TypeDecorator, func
from sqlalchemy.dialects.postgresql import JSONB


# Column helpers
def make_timestamptz() -> DateTime:
    return DateTime(timezone=True)


def make_enum(enum_cls) -> ENUM:
    """Helper class to create an enum column that is stored as a VARCHAR"""
    return ENUM(
        enum_cls,
        create_constraint=False,
        native_enum=False,
        length=255,
    )


# Custom column types
class DataclassJSONB(TypeDecorator):
    """Serializes and deserializes a dataclass and saves it as JSONB.
    Implements the JSONB column type.

    Use @dataclass_json for objects with nested dataclass or inherit DataClassJsonMixin
    Ex.
    @dataclass_json
    @dataclass
    class MyObject:
        prop1: str
        nested_dataclass: OtherDataclass
    OR
    @dataclass
    class MyObject(DataClassJsonMixin):
        ...
    """

    impl = JSONB

    def __init__(self, my_dataclass):
        self.my_dataclass = my_dataclass
        super().__init__()

    def convert_enum_values_to_string(self, data: dict) -> dict:
        if isinstance(data, dict):
            return {
                self.convert_enum_values_to_string(k): self.convert_enum_values_to_string(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self.convert_enum_values_to_string(item) for item in data]
        elif isinstance(data, Enum):
            return data.value
        else:
            return data

    def process_bind_param(self, value, _):
        if value is not None:
            value = self.convert_enum_values_to_string((asdict(value)))
        return value

    def process_result_value(self, value, _):
        if value is not None:
            if hasattr(self.my_dataclass, "from_dict"):
                # use dataclass_json from dict as it handles nested dataclass
                return self.my_dataclass.from_dict(value)
            else:
                return self.my_dataclass(**value)

        return value


class EnumListJSONB(TypeDecorator):
    """Deserializes a list of enum objects and returns the enum names in a list"""

    impl = JSONB

    def __init__(self, my_enum: Type[Enum]):
        self.my_enum = my_enum
        super().__init__()

    def process_bind_param(self, enums, _) -> Optional[list]:
        if enums is not None:
            return [item.value for item in enums]
        return enums

    def process_result_value(self, enums, _) -> Optional[list]:
        if enums is not None:
            return [self.my_enum(enum) for enum in enums]

        return enums


# Mixins
class CreatedAtMixin:
    created_at = Column(
        make_timestamptz(),
        server_default=func.current_timestamp(),
        nullable=False,
        doc="Time at which the row was created.",
    )


class UpdatedAtMixin:
    updated_at = Column(
        make_timestamptz(),
        server_default=func.current_timestamp(),
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Time at which the row was updated.",
    )


class CreatedAtUpdatedAtMixin(CreatedAtMixin, UpdatedAtMixin):
    pass
