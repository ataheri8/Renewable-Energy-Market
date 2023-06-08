import logging

from pythonjsonlogger import jsonlogger  # type: ignore

from shared.system.configuration import Config


def init(config: Config):
    # Debug python logging:
    # from logging_tree import printout; printout()

    # Configure logging (root)
    logging.basicConfig(level=logging.DEBUG)

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        # Propagate all loggers to the root logger so no messages are lost when we remove
        # the handler below
        logger.propagate = True

        # Remove all child handlers so we can control output + format + no dup. log entries
        for handler in logger.handlers:
            logger.removeHandler(handler)

    if not config.DEV_MODE:
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        # Configure JSON logging
        class CustomJsonFormatter(jsonlogger.JsonFormatter):
            def parse(self):
                return ["asctime", "levelname", "filename", "name", "message"]

        handler = root.handlers[0]
        handler.setFormatter(CustomJsonFormatter())


def get_logger(name: str = ""):
    return logging.getLogger(name)
