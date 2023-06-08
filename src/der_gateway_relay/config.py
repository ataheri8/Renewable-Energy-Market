from shared.system.configuration import Config


class DerGatewayRelayConfig(Config):
    DER_GATEWAY_URL: str = "http://localhost:8080"
    DER_GATEWAY_PROGRAM_TOPIC: str = "der-gateway-program"
