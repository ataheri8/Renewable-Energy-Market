import argparse
import logging
import os

from dotenv import load_dotenv

from pm.config import PMConfig
from pm.consumers.contract import handlers as contract_handlers  # noqa
from pm.consumers.der_gateway import handlers as der_gateway_handlers  # noqa
from pm.consumers.der_warehouse import handlers as der_handlers  # noqa
from pm.consumers.event import (  # noqa
    handle_enrollment_create_message as enrollment_handlers,
)
from pm.consumers.event import (  # noqa
    handle_service_provider_der_association_message as service_provider_der_handler,
)
from pm.consumers.event import handlers as event_handlers  # noqa

# import tasks that need to be registered. Consumer won't show without importing it here
# ie: for this to work @register_topic_handler
# models
from pm.modules.enrollment.models import *  # noqa
from pm.modules.event_tracking.models import *  # noqa
from pm.modules.outbox.model import *  # noqa
from pm.modules.progmgmt.models import *  # noqa
from pm.modules.serviceprovider.models import *  # noqa
from shared.system import configuration, database, loggingsys
from shared.tasks.consumer import (
    BatchMessageConsumer,
    Consumer,
    SingleMessageConsumer,
    create_kafka_topics,
)

# load env variables
load_dotenv()
config = configuration.init_config(PMConfig)

# setup logging
loggingsys.init(config=config)

# set the overly chatty kafka logs to show errors only
kafka3_log = loggingsys.get_logger("kafka3")
kafka3_log.setLevel(logging.ERROR)
kafka_log = loggingsys.get_logger("kafka")
kafka_log.setLevel(logging.ERROR)

# init SQL Alchemy
database.init(config=config)

logger = loggingsys.get_logger(name=__name__)
logger.info("Starting worker...")

# Consumer type constants
BATCH_CONSUMER = "batch"
SINGLE_CONSUMER = "single"

MAX_BULK_MESSAGES = 1000

# Consumer type env variable constants
INCLUDE_TOPICS = "INCLUDE_TOPICS"
CONSUMER_TYPE = "CONSUMER_TYPE"


def split_and_strip(s: str) -> list[str]:
    return [t.strip() for t in s.split(",")]


def parse_arguments() -> dict:
    """Parse command line arguments or environment variables.
    The following command line arguments are available:
    --include-topics: A comma separated list of topics to include.
    --bulk-ingest: A boolean flag to enable bulk ingestion.

    The following environment variables are available:
    INCLUDE_TOPICS: A comma separated list of topics to include.
    CONSUMER_TYPE: A string to set the worker type. Options are "batch" or "single".
    Will default to "single".
    """
    parser = argparse.ArgumentParser(description="PM Worker")
    parser.add_argument(
        "--include-topics",
        type=str,
        help="A comma separated list of topics to include.",
    )
    parser.add_argument(
        "--consumer-type",
        choices=[BATCH_CONSUMER, SINGLE_CONSUMER],
        default=SINGLE_CONSUMER,
        help="The consumer type. Default is 'single'.",
    )
    args = parser.parse_args()
    parser
    include_topics = os.getenv(INCLUDE_TOPICS, args.include_topics)
    consumer_type = os.getenv(CONSUMER_TYPE, args.consumer_type)
    if include_topics:
        include_topics = split_and_strip(include_topics)
    return {
        "include_topics": include_topics,
        "consumer_type": consumer_type,
    }


if __name__ == "__main__":
    if config.DEV_MODE:
        # create topics if they don't exist, dev mode only
        create_kafka_topics(config.KAFKA_URL)

    settings = parse_arguments()
    consumer: Consumer
    logger.info(f"Starting {settings['consumer_type']} consumer...")
    if settings["consumer_type"] == BATCH_CONSUMER:
        consumer = BatchMessageConsumer.factory(
            group_id=config.KAFKA_GROUP_ID,
            url=config.KAFKA_URL,
            include_topics=settings["include_topics"],
            max_bulk_messages=MAX_BULK_MESSAGES,
        )
    elif settings["consumer_type"] == SINGLE_CONSUMER:
        consumer = SingleMessageConsumer.factory(
            group_id=config.KAFKA_GROUP_ID,
            url=config.KAFKA_URL,
            include_topics=settings["include_topics"],
        )
    else:
        raise ValueError(
            f"Invalid consumer type '{settings['consumer_type']}'. Must be 'batch' or 'single'."
        )
    consumer.listen()
