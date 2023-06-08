from __future__ import annotations

import os
import sys
from dataclasses import dataclass, fields
from typing import Optional, Type

CONFIG: Optional[Config] = None


class ConfigNotInitialized(Exception):
    pass


@dataclass
class Config:
    DEV_MODE: bool = True
    OFFLINE_MODE: bool = False

    DER_WAREHOUSE_URL: str = ""
    DER_GATEWAY_URL: str = "http://localhost:8080"
    ALS_URL: str = "http://localhost:3003"

    KAFKA_URL: str = ""
    KAFKA_GROUP_ID: str = ""

    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_NAME: str = ""
    MINIO_END_POINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_SOURCE_FOLDER: str = "target"
    MINIO_PROCESSED_FOLDER: str = "processed"

    DB_PORT: int = 5432

    CSV_INGESTION_TOPIC = "CSV_INGESTION_TOPIC"
    PAGINATION_DEFAULT_LIMIT: int = 1000  # default number of items per page allowed by the system.
    PAGINATION_MAX_LIMIT: int = 10000  # maximum items per page allowed by the system.

    MAX_HOL_CAL_FILE_SIZE: int = 10000

    @classmethod
    def from_env(cls) -> Config:
        envs_defined: dict = {}
        for f in fields(Config):
            val = None
            match f.type:
                case "bool":
                    val = env_flag(f.name)
                case "int":
                    val = os.environ.get(f.name)
                    val = int(val) if val else None
                case "str":
                    val = os.environ.get(f.name)
            if val is not None:
                envs_defined[f.name] = val

        try:
            return cls(**envs_defined)
        except ValueError:
            print("Unable to load Config. -- value type missmatch (ie. got str when int expected).")
            sys.exit(1)


def get_config() -> Config:
    if CONFIG is None:
        raise ConfigNotInitialized()
    return CONFIG


def init_config(MyConfig: Type[Config]) -> Config:
    global CONFIG
    CONFIG = MyConfig.from_env()
    return CONFIG


# Helpers & Utils
# ---------------
def env_flag(env_var: str, default: bool = False) -> bool:
    """
    Return the specified environment variable coerced to a bool, as follows:
    - When the variable is unset, or set to the empty string, return `default`.
    - When the variable is set to a truthy value, return `True`.
      These are the truthy values:
          - 1
          - true, yes, on
    - When the variable is set to the anything else, returns False.
       Example falsy values:
          - 0
          - no
    - Ignore case and leading/trailing whitespace.

    Note: Taken from (unmaintained): https://github.com/metabolize/env-flag/blob/master/env_flag/__init__.py  # noqa: E501
    """
    environ_string = os.environ.get(env_var, "").strip().lower()
    if not environ_string:
        return default
    return environ_string in ["1", "true", "yes", "on"]
