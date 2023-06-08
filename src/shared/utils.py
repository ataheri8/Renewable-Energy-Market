import functools
from datetime import datetime
from enum import Enum
from typing import Any


def recursive_getattr(obj: object, attributes: str):
    """Recurvisly get an attribute from an object.
    Useful for getting attributes from nested objects.

    Example:
        recursive_getattr(obj, "a.b.c")
    """
    return functools.reduce(getattr, attributes.split("."), obj)


def convert_datetimes_and_enums_to_string(data: Any) -> Any:
    """Converts datetime and enum values to string."""
    if isinstance(data, dict):
        return {
            convert_datetimes_and_enums_to_string(k): convert_datetimes_and_enums_to_string(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [convert_datetimes_and_enums_to_string(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, Enum):
        return data.value
    else:
        return data
