import enum


class ServiceProviderType(enum.Enum):
    AGGREGATOR = "AGGREGATOR"
    C_AND_I = "C_AND_I"
    RESIDENTIAL = "RESIDENTIAL"


class ServiceProviderStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
