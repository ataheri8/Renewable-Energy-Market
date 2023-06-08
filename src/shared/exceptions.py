from typing import Optional

from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


class Error(Exception):
    """Base class for exceptions.
    Accepts optional message (string) and errors (dict) arguments.
    """

    def __init__(self, message="", errors: Optional[dict] = None) -> None:
        self.errors = errors
        self.message = message
        super().__init__(message)


class LoggedError(Error):
    def __init__(self, message, *args, **kwargs):
        logger.error(message)
        super().__init__(message, *args, **kwargs)
