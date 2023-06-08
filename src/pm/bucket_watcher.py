import csv
import io
from itertools import islice, zip_longest
from typing import Generator, Iterable

from confluent_kafka.error import ProduceError
from dotenv import load_dotenv
from marshmallow import ValidationError

from pm.config import PMConfig
from pm.modules.enrollment.models import *  # noqa
from pm.modules.progmgmt.models import *  # noqa
from pm.modules.serviceprovider.models import *  # noqa
from shared.minio_manager import Message, MinioManager
from shared.system import configuration, loggingsys

load_dotenv()
config = PMConfig.from_env()
loggingsys.init(config)

logger = loggingsys.get_logger(__name__)


def batched(iterable, n):
    """Batch data into lists of length n. The last batch may be shorter.
    see https://docs.python.org/3/library/itertools.html#itertools-recipes"""

    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            return
        yield batch


def grouper(iterable, n, *, incomplete="fill", fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == "fill":
        return zip_longest(*args, fillvalue=fillvalue)
    if incomplete == "strict":
        return zip(*args, strict=True)
    if incomplete == "ignore":
        return zip(*args)
    else:
        raise ValueError("Expected fill, strict, or ignore")


class ExtractCSVrows:
    """Context manager : given a filename, extract each row as a dict for sending off to a topic"""

    message_class: Message
    file_handle: io.StringIO
    input_file: csv.DictReader

    def __init__(self, file_name: str, path: str):
        file_manager = MinioManager(bucket_name=path)
        config = configuration.get_config()
        try:
            file_tag = file_manager.get_file_type_tag(
                bucket_name=path,
                file_name=file_name,
            )
            self.message_class: Message = Message.get_matching_class_label(
                class_label_to_check=file_tag
            )
            self.file_handle = file_manager.get_string_io(file_name)
            self.input_file = csv.DictReader(self.file_handle)
        except (ValidationError, UnicodeDecodeError) as e:
            logger.error(f"34:file {file_name} error: {e}")
            file_manager.move_file(
                source_bucket=path,
                source_filename=file_name,
                destination_bucket=config.MINIO_PROCESSED_FOLDER,
                destination_filename=file_name,
            )
            logger.info(f"39: moved file '{file_name}' to bucket '{config.MINIO_PROCESSED_FOLDER}'")
            raise e

    def __enter__(self) -> Generator[dict, None, None]:
        for row in self.input_file:
            yield row

    def __exit__(self, type, value, traceback):
        self.file_handle.close()


def listen_to_bucket_process_rows():
    config = configuration.get_config()
    file_manager = MinioManager(bucket_name=config.MINIO_SOURCE_FOLDER)
    for file_name in file_manager.listen_bucket_notification():
        csv_rows_as_dicts_generator = ExtractCSVrows(
            file_name=file_name,
            path=config.MINIO_SOURCE_FOLDER,
        )
        tags = file_manager.get_tags(file_name=file_name)
        with csv_rows_as_dicts_generator as row_generator:
            message_class = csv_rows_as_dicts_generator.message_class
            success = send_batches_to_kafka(message_class, row_generator, tags)
            if not success:
                add_fail_status_minio_tag(file_manager, file_name)
        move_file_to_destination(
            config.MINIO_SOURCE_FOLDER,
            file_name,
            config.MINIO_PROCESSED_FOLDER,
        )


def add_fail_status_minio_tag(file_manager, file_name):
    # we only add 'fail'tags, which means we don't have to track status quite as much
    # we might be adding fail tags repeatedly to files already marked fail

    file_manager.add_tags(
        file_name=file_name,
        new_tags={"process_successful": "false"},
    )


def send_batches_to_kafka(
    message_class: Message,
    row_generator: Iterable,
    tags: dict,
) -> bool:
    file_processed_successfully = True
    for batch_number, row_batch in enumerate(
        batched(
            row_generator,
            message_class.Meta.batch_size,
        )
    ):
        try:
            batch_data = [
                message_class.message_factory(
                    row,
                    row_number,
                    batch_number,
                    tags,
                )
                for row_number, row in enumerate(
                    row_batch,
                    start=1,
                )
            ]
            if None in batch_data:
                # at least one row failed
                file_processed_successfully = False
                batch_data.remove(None)

            if batch_data:
                message_class.send_batch_to_kafka(batch_data)
                message_class.flush_kafka()
            message_class.send_progress_notification(batch_number=batch_number, tags=tags)
        except (ProduceError, ValidationError, KeyError) as e:
            logger.error(f"129: csv processing error: {e}")
            file_processed_successfully = False
            continue
    return file_processed_successfully


def move_file_to_destination(
    source_bucket: str,
    filename: str,
    processed_destination_bucket: str,
    file_manager=MinioManager,
) -> None:
    try:
        file_manager().move_file(
            source_bucket=source_bucket,
            source_filename=filename,
            destination_bucket=processed_destination_bucket,
            destination_filename=filename,
        )
    except Exception as e:
        logger.error("147:error moving file: %s", filename)
        logger.error(e)


def initialize_buckets(file_manager: MinioManager | None = None):
    """create if not exists the buckets we need"""
    file_manager = file_manager or MinioManager()
    config = configuration.get_config()
    for bucket in [
        config.MINIO_SOURCE_FOLDER,
        config.MINIO_PROCESSED_FOLDER,
    ]:
        file_manager.ensure_bucket_exists(bucket_name=bucket)


def main_file_watcher():
    logger.info("starting file watcher...")
    initialize_buckets()
    while True:
        try:
            listen_to_bucket_process_rows()
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    main_file_watcher()
