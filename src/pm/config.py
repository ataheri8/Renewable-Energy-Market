from dataclasses import dataclass

from shared.system.configuration import Config


@dataclass
class PMConfig(Config):
    MAX_HOL_CAL_FILE_SIZE: int = 1 * 1024 * 1024  # 1 Megabyte

    DB_NAME: str = "pmcore"
