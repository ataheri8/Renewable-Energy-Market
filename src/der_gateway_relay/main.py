from dotenv import load_dotenv

from der_gateway_relay.config import DerGatewayRelayConfig
from der_gateway_relay.consumer import handle_der_gateway_program  # noqa
from shared.system import configuration, loggingsys
from shared.tasks.consumer import BatchMessageConsumer

load_dotenv()

config = configuration.init_config(DerGatewayRelayConfig)
loggingsys.init(config)
logger = loggingsys.get_logger(__name__)

MAX_MESSAGES = 1
TIMEOUT_SECONDS = 1
CONSUMER_GROUP = "der-gateway-relay"


if __name__ == "__main__":
    logger.info("Starting DER Gateway Relay Consumer...")
    consumer = BatchMessageConsumer.factory(
        url=config.KAFKA_URL,
        group_id=CONSUMER_GROUP,
        max_bulk_messages=MAX_MESSAGES,
        bulk_timeout_seconds=TIMEOUT_SECONDS,
    )
    consumer.listen()
