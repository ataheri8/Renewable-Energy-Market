from http import HTTPStatus

from flask_smorest import abort  # type: ignore

from shared.exceptions import Error
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


def raise_error(status: HTTPStatus, err: Error):
    """Abort the API call and return a payload with details about the HTTP error raised.
    The stack trace will be printed and the 'message' and 'errors' fields on Error will
    be appended to the response.
    """
    logger.error(err, exc_info=True)
    abort(
        status,
        errors=err.errors,
        code=status.value,
        message=str(err),
        status=status.phrase,
    )


def raise_custom_error(status: HTTPStatus, **kwargs):
    """
    PARAMS:
    status: Http status code
    kwargs: Must contain a message along with custom keyword args

    Abort the API call and return payload with HTTP error raised.
    Use this method for Custom or prebuilt errors
    which internally inherits BaseException instead of Error class
    examples: S3Error, ServerError from minio lib
    """
    logger.error(kwargs["message"], exc_info=True)
    abort(status, **kwargs)
