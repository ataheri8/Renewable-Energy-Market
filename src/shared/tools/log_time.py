import functools
from logging import Logger
from typing import Optional

import pendulum


def log_time(logger: Logger, warn_minutes: Optional[int] = 5):
    """Log the time it takes a function to run in milliseconds."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper_log_time(*args, **kwargs):
            SECONDS_IN_MINUTE = 60
            start_time = pendulum.now()
            result = func(*args, **kwargs)
            end_time = pendulum.now()
            time_taken = end_time - start_time
            logger.info(f"{func.__name__} finished in {time_taken.microseconds / 1000}ms")
            if time_taken.seconds / SECONDS_IN_MINUTE > warn_minutes:
                logger.warning(
                    f"Function {func.__name__} took more than {warn_minutes} minutes to run"
                )
            return result

        return wrapper_log_time

    return decorator
