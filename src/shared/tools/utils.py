import datetime
from typing import Callable

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from shared.exceptions import LoggedError
from shared.system.loggingsys import get_logger

logger = get_logger(__name__)


def generate_timestamp() -> str:
    """this is a function so we can mock it in tests"""
    return datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")


def generate_safe_unique_file_name(
    file_name: str,
    timestamp_generation_function: Callable = generate_timestamp,
) -> str:
    """
    given a file name, append a timestamp to the name and preserve the file extension
    Note we can pass in a function to generate the timestamp, so we can test this function
    >>> generate_safe_unique_file_name('file.csv')
    'file.2020-01-01T00-00-00-000000.csv'
    >>> generate_safe_unique_file_name('foo.bar.baz.csv')
    'foo.bar.baz.2020-01-01T00-00-00-000000.csv'
    >>> generate_safe_unique_file_name('foo')
    'foo.2020-01-01T00-00-00-000000'
    """
    try:
        file_name = secure_filename(file_name)
        filename_pieces = str(file_name).split(".")
    except Exception:
        filename_pieces = [str(file_name)]
    timestamp: str = timestamp_generation_function()
    if len(filename_pieces) > 1:
        filename_pieces.insert(-1, timestamp)
    else:
        filename_pieces.append(timestamp)
    return ".".join(filename_pieces)


def is_csv(file: FileStorage):
    if not secure_filename(file.filename).endswith(".csv"):  # type: ignore # noqa [union-attr]
        raise LoggedError("Invalid file extension. Only CSV allowed")
    lines = len(file.readlines())
    return lines


def validate_uploaded_csv_and_row_count(file: FileStorage) -> int:
    if not file:
        raise LoggedError("Missing File")
    no_of_rows = is_csv(file)
    return no_of_rows


def convert_from_snake_to_camel_case(text: str):
    string = "".join(word.title() for word in text.split("_"))
    return string[0].lower() + string[1:]
