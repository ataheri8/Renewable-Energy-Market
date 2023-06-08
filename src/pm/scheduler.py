import time

import pendulum
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from pm.config import PMConfig
from pm.modules.enrollment.contract_controller import ContractController  # noqa

# models
from pm.modules.enrollment.models import *  # noqa
from pm.modules.event_tracking.controller import EventController
from pm.modules.outbox.controller import OutboxController
from pm.modules.progmgmt.controller import ProgramController
from pm.modules.progmgmt.models import *  # noqa
from pm.modules.serviceprovider.models import *  # noqa
from shared.system import configuration, database, loggingsys
from shared.tools.log_time import log_time

# load env variables
load_dotenv()
config = configuration.init_config(PMConfig)

# setup logging
loggingsys.init(config=config)

# init SQL Alchemy
database.init(config=config)

logger = loggingsys.get_logger(name=__name__)
logger.info("Starting scheduler...")


@log_time(logger)
def check_for_kafka_messages():
    """Check for new messages in the Kafka topic and process them."""
    OutboxController().send_message()


@log_time(logger)
def calculate_daily_constraints():
    """Calculate the daily contract constraints for the previous day.
    Aggregates event data from DER Gateway per contract.
    """
    yesterday = pendulum.now().subtract(days=1)
    EventController().calculate_contract_constraints(yesterday)


@log_time(logger)
def update_program_status():
    """Update program status based on current date.
    Published programs with a start date in the past are activated.
    Active programs with an end date in the past are archived.
    """
    controller = ProgramController()
    controller.activate_programs()
    controller.archive_expired_programs()


@log_time(logger)
def update_contract_status():
    """Update contract status based on program status.
    Activate contract if associated program is set to Active
    Expired contract if associated program is set to Archive
    """
    controller = ContractController()
    controller.activate_contracts()
    controller.expire_contracts_archived_programs()


def init_scheduler():
    """Initialize the scheduler and start the background tasks.

    The default scheduler uses a ThreadPoolExecutor with 10 workers,
    and it will run until the app is shut down.

    See: https://apscheduler.readthedocs.io/en/stable/userguide.html#background-scheduler
    """
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(check_for_kafka_messages, "interval", seconds=5)
    scheduler.add_job(calculate_daily_constraints, "cron", hour=2)
    scheduler.add_job(update_program_status, "interval", hours=1)

    try:
        while True:
            time.sleep(1)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    init_scheduler()
