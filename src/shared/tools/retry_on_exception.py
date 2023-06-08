import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple

from shared.system import loggingsys

logger = loggingsys.get_logger(__name__)


def retry_on_exception(
    num_retries: int = 3, backoff: float = 0, errors: Optional[Tuple] = None
) -> Callable:
    """Retries a function with a backoff up to `num_retries` times if it raises an exception.
    On the last retry, the exception will be raised so it can be caught by the caller. Optionally,
    you can specify types of errors to catch. If not specified, it will catch all exceptions.
    """

    def decorator_retry_on_exception(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper_retry_on_exception(*args: Any, **kwargs: Any) -> Any:
            for i in range(num_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if errors is None or isinstance(e, errors):
                        if i == num_retries - 1:
                            raise e
                        else:
                            sleep_for = backoff * (i + 1)
                            logger.warning(f"{e} Retry in {sleep_for} seconds", exc_info=True)
                            time.sleep(sleep_for)
                    else:
                        # if the error is not in the list of errors to catch, raise it
                        raise e

        return wrapper_retry_on_exception

    return decorator_retry_on_exception
