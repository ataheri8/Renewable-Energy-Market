from __future__ import annotations

import csv
import enum
import io
import logging
import os
import time
from dataclasses import dataclass, fields
from io import BytesIO
from typing import Any, Dict, Generator, List, Optional

from dataclasses_json import DataClassJsonMixin
from dataclasses_json.core import _asdict
from dotenv import load_dotenv
from marshmallow import ValidationError
from minio import Minio
from minio.api import ObjectWriteResult
from minio.commonconfig import CopySource, Tags
from minio.error import S3Error
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from pm.config import PMConfig
from shared.system import configuration
from shared.tasks.producer import Producer
from shared.tools.utils import (
    generate_safe_unique_file_name,
    validate_uploaded_csv_and_row_count,
)

DEFAULT_BATCH_MESSAGE_SIZE = 50

FILE_TYPE_TAG = "FILE_TYPE"

logger = logging.getLogger(__name__)


def convert_strings_to_float(value: str) -> Optional[float]:
    """convert a string to a float, or return None if the string is empty
    >>> convert_strings_to_float("1.0")
    1.0
    >>> convert_strings_to_float("")
    None
    >>> convert_strings_to_float("abc")
    ValidationError: Invalid :abc not a float
    """
    if value == "" or value.isspace():
        return None
    try:
        return float(value)
    except ValueError:
        raise ValidationError(f"Invalid :{value} not a float")


def check_value_is_allowed_by_enum(supplied_value, enum_type: enum.EnumMeta):
    if supplied_value not in enum_type.__members__.keys():
        raise ValidationError(f"Invalid :{supplied_value} not a {enum_type}")


class Message:
    __headers__: dict

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls.Meta, "topic"):
            raise ValidationError(f"Invalid :{cls.__name__} must have a topic in Meta")
        if not hasattr(cls, "__headers__"):
            cls.__headers__ = {}
        if not hasattr(cls.Meta, "batch_size"):
            cls.Meta.batch_size = DEFAULT_BATCH_MESSAGE_SIZE
        return super().__new__(cls)

    class Meta:
        topic: str
        batch_size: int

    @property
    def headers(self):
        # convenience shortcut property
        return self.__headers__

    def set_headers(self, headers: dict):
        self.__headers__ = headers

    def process_message(self):
        """override in the subclass -  use it in the kafka consumer
        e.g.  called in a function decorated with @register_topic_handler
        """
        raise NotImplementedError

    @classmethod
    def process_messages(cls, list_of_messages: List["Message"]):
        """override in the subclass for batch processing: ie to use
        batch SQL inserts instead of one at a time"""
        for message in list_of_messages:
            message.process_message()

    @classmethod
    def get_class_label(cls):
        """minio needs a tag to identify the type of csv file this message is for
        by default the name of the class , but override in the subclass as req.
        The label returned should match the FILE_TYPE tag passed from the API"""
        return cls.__name__

    @classmethod
    def get_filename(cls):
        """
        generates csv filename by getting class label.
        get_class_label can return user defined class label
        """
        return f"{cls.get_class_label()}_template.csv"

    @classmethod
    def get_all_message_classes(cls):
        return cls.__subclasses__()

    @classmethod
    def get_matching_class_label(cls, class_label_to_check: str):
        # For subclass detection from another module
        from pm.data_transfer_objects import csv_upload_kafka_messages  # noqa

        for subclass in cls.get_all_message_classes():
            if subclass.get_class_label() == class_label_to_check:
                return subclass
        raise ValidationError(f"Invalid :'{class_label_to_check}' not a valid message type")

    @classmethod
    def batch_set_header(cls, list_of_messages, header):
        # given a dict and a list of messages, apply the headers to all of them
        #  if there's already a header, merge with it : preference to the current header values;
        [ele.set_headers({**header, **ele.headers}) for ele in list_of_messages]
        # this is 'in place' altering so no need to return anything, but for convenience:
        return list_of_messages

    def send_to_kafka(self):
        Producer.send_message(
            message=self,
            topic=self.Meta.topic,
            headers=self.headers,
        )

    @classmethod
    def send_batch_to_kafka(cls, list_of_messages):
        """Send a batch of messages to kafka
        :param list_of_messages: list[Message]
        Note we use the first item's Meta for the message headers and topic
        """
        json_data: str = cls.schema().dumps(list_of_messages, many=True)  # type: ignore
        last_message = list_of_messages[-1]
        Producer.send_json(
            json_str=json_data,
            topic=last_message.Meta.topic,
            headers=last_message.headers,
        )

    @classmethod
    def flush_kafka(cls):
        Producer.flush()

    def to_dict(self, encode_json=False) -> Dict[Any, Any]:
        # we want the field names, not the metadata field names read in from the XML
        # if we don't use metadata=config( field_name="XXXX") in the field definition
        # then this does nothing
        data = {attr_name: field_obj for attr_name, field_obj in self.__dict__.items()}
        return _asdict(data, encode_json=encode_json)

    @classmethod
    def message_factory(
        cls,
        row: dict,
        row_number: int = 0,
        batch_number: int = 0,
        tags: dict | None = None,
    ) -> Message | None:
        """
        Create a schema-validated message object from a row of data
        return None if the row is invalid
        """
        tags = tags or {}
        try:
            data: Message = cls.schema().load(row)  # type: ignore
        except ValidationError as e:
            logger.error(f"Error validating row {row_number} :{e}")
            cls.handle_error_row(batch_number, {"row_data": row})
            return None
        additional_headers: dict = cls.generate_progress_data(batch_number, row_number)
        data.set_headers({**tags, **data.headers, **additional_headers})
        return data

    @classmethod
    def _send_notification(
        cls,
        notification_type: str,
        batch_number: int,
        tags: Optional[dict] = None,
    ):
        tags = tags or {}
        tags.update(
            cls.generate_progress_data(
                batch_number,
                cls.Meta.batch_size,
            )
        )
        notification = Notification(
            session_id=tags.get("session_id", "session_id not supplied"),
            notification_type=notification_type,
            additional_data=tags,
        )
        notification.set_headers(tags)
        notification.send_to_kafka()
        return notification

    @classmethod
    def generate_progress_data(cls, batch_number: int, row_number: int) -> dict:
        additional_headers = {
            "topic": cls.Meta.topic,
            "batch_size": cls.Meta.batch_size,
            "batch_number": batch_number,
            "row_number": (batch_number * cls.Meta.batch_size) + row_number,
        }
        return additional_headers

    @classmethod
    def send_progress_notification(
        cls,
        batch_number: int,
        tags: dict | None = None,
    ) -> Notification:
        """
            Send a progress_notification to kafka for FE to update the UI:
        we need a session_Id in the header
        to be able to link the progress_notification to the FE user session
        """
        tags = tags or {}
        return cls._send_notification(
            notification_type="progress",
            batch_number=batch_number,
            tags=tags,
        )

    @classmethod
    def handle_error_row(
        cls,
        batch_number: int,
        tags: dict | None = None,
    ) -> Notification:
        """
            Send a error notification to kafka for FE to update the UI:
        we need a session_Id in the header
        to be able to link the progress_notification to the FE user session
        """
        tags = tags or {}
        return cls._send_notification("error", batch_number, tags)

    @classmethod
    def get_template_headers(cls) -> list[str]:
        headers = list()
        for f in fields(cls):  # type: ignore[arg-type]
            try:
                headers.append(f.metadata["dataclasses_json"]["letter_case"](f.name))
            except KeyError:
                headers.append(f.name)
        return headers

    @classmethod
    def generate_csv_template(cls) -> io.BytesIO:
        header_fields = cls.get_template_headers()
        filename = cls.get_filename()
        data = io.StringIO()
        csv.writer(data).writerow(header_fields)
        buf = io.BytesIO()
        buf.write(data.getvalue().encode("utf-8-sig"))
        buf.seek(0)
        buf.name = filename
        return buf


@dataclass
class FakeMessage(Message, DataClassJsonMixin):
    program_id: int

    class Meta:
        topic = "fakeTopic"

    def process_message(self):
        print("process_message")

    def send_batch_to_kafka(self):
        print("162: send_batch_to_kafka: FakeMessage")


@dataclass
class Notification(Message, DataClassJsonMixin):
    class Meta:
        NotificationType = "Update"
        topic = "notifications"
        batch_size = 1

    session_id: int
    additional_data: dict
    timestamp: int = 0
    notification_type: str = Meta.NotificationType

    def __post_init__(self, *args, **kwargs):
        self.timestamp = int(time.time())


@dataclass
class EnrollmentMessage(Message, DataClassJsonMixin):
    program_id: int
    enrollment_program_type: str
    enrollment_status: str
    enrollment_contract_type: str
    service_provider: str
    der_id: str
    contract_status: str

    class Meta:
        topic = "pm.enrollment"

    def process_message(self):
        print("process_message")


class MinioManager:
    access_key: str = ""
    secret_key: str = ""
    end_point: str = ""
    secure: bool = False
    bucket_name: str = "target"

    def __init__(
        self,
        bucket_name: str = "target",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        end_point: Optional[str] = None,
    ):
        load_dotenv()
        config = configuration.init_config(PMConfig)
        self.bucket_name = bucket_name
        self.access_key = access_key or config.MINIO_ACCESS_KEY
        self.secret_key = secret_key or config.MINIO_SECRET_KEY
        self.end_point = end_point or config.MINIO_END_POINT
        self.client = Minio(
            self.end_point,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=self.secure,
        )

    def create_bucket(self, bucket_name: str = ""):
        bucket_name = bucket_name or self.bucket_name
        self.client.make_bucket(bucket_name)
        self.bucket_name = bucket_name

    def delete_bucket(self, bucket_name: str):
        # bucket must be empty to delete it
        self.client.remove_bucket(bucket_name)

    def list_buckets(self):
        return [bucket.name for bucket in self.client.list_buckets()]

    def does_bucket_exist(self, bucket_name: str):
        return self.client.bucket_exists(bucket_name)

    def create_tag_object(self, tags: dict) -> Tags:
        minio_tags = Tags.new_object_tags()
        for key, value in tags.items():
            minio_tags[key] = str(value)
        return minio_tags

    def get_string_io(self, file_name: str) -> io.StringIO:
        response = self.client.get_object(self.bucket_name, file_name)
        return io.StringIO(response.data.decode("UTF-8-sig"))

    def get_byte_io(self, file_name: str) -> BytesIO:
        response = self.client.get_object(self.bucket_name, file_name)
        return io.BytesIO(response.data)

    def get_file_size(self, file_name: str) -> int:
        response = self.client.stat_object(self.bucket_name, file_name)
        return response.size

    def put_filehandle(
        self,
        file_name: str,
        file_data: io.BytesIO,
        tags: dict | None = None,
    ) -> ObjectWriteResult:
        file_data.seek(0, io.SEEK_END)
        length = file_data.tell()
        file_data.seek(0, io.SEEK_END)
        data = file_data.getvalue()
        tags = self.create_tag_object(tags or {})
        return self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=file_name,
            data=io.BytesIO(data),
            length=length,
            tags=tags,
        )

    def put_file(self, file_path: str = "", tags: dict | None = None) -> ObjectWriteResult:
        fn = os.path.basename(file_path)
        tags = self.create_tag_object(tags or {})
        return self.client.fput_object(
            bucket_name=self.bucket_name,
            object_name=fn,
            file_path=file_path,
            tags=tags,
        )

    def list_files(self, bucket_name: str = "") -> list[str]:
        bucket_name = bucket_name or self.bucket_name
        return [obj.object_name for obj in self.client.list_objects(bucket_name)]

    def get_tags(self, file_name: str, bucket_name: str = "") -> dict:
        bucket_name = bucket_name or self.bucket_name
        try:
            tags: Tags = self.client.get_object_tags(bucket_name=bucket_name, object_name=file_name)
            if tags is None:
                return {}
            return dict(tags)
        except TypeError as err:
            raise ValidationError(f"421: Tag Error: {err}")

    def get_file_type_tag(self, file_name: str, bucket_name: str = "") -> str:
        file_type: str = self.get_specific_tag(
            tag_name=FILE_TYPE_TAG, file_name=file_name, bucket_name=bucket_name
        )
        if not file_type:
            raise ValidationError(f"416: File Type Tag Not Set: {file_name}")
        return file_type

    def get_specific_tag(self, tag_name: str, file_name: str, bucket_name: str = "") -> str:
        tags = self.get_tags(file_name=file_name, bucket_name=bucket_name)
        return tags.get(tag_name, "")

    def add_tags(self, file_name: str, new_tags: dict) -> None:
        # given an already existing file, with tags, add new tags to it
        current_tags = self.get_tags(file_name=file_name)
        tags = self.create_tag_object({**current_tags, **new_tags})
        self.client.set_object_tags(self.bucket_name, file_name, tags)

    def delete_file(self, file_name: str) -> None:
        return self.client.remove_object(self.bucket_name, file_name)

    def generate_list_file_names(self, bucket_name: str = "") -> Generator[str, None, None]:
        bucket_name = bucket_name or self.bucket_name
        for file in self.client.list_objects(bucket_name=bucket_name):
            yield file.object_name

    def listen_bucket_notification(self):
        # see https://gist.github.com/ruanbekker/dc3c8d2258f66045330bed9985c3c459
        # first lets process files already in the bucket
        yield from self.generate_list_file_names()
        # now listen for new files
        with self.client.listen_bucket_notification(
            self.bucket_name,
            events=["s3:ObjectCreated:*"],
        ) as events:
            for event in events:
                for record in event["Records"]:
                    yield record["s3"]["object"]["key"]

    def move_file(
        self,
        source_bucket: str,
        source_filename: str,
        destination_bucket: str,
        destination_filename: str,
    ) -> None:
        """this assumes the destination bucket exists"""
        self.client.copy_object(
            bucket_name=destination_bucket,
            object_name=destination_filename,
            source=CopySource(
                source_bucket,
                source_filename,
            ),
        )
        return self.client.remove_object(
            bucket_name=source_bucket,
            object_name=source_filename,
        )

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            self.create_bucket(bucket_name=bucket_name)
        except S3Error:
            logger.info(f"Bucket {bucket_name} already exists")

    def upload_csv_to_minio(self, file: FileStorage, tags: dict):
        """
        tags: dictionary of tags to be passed to minio
        e.g: tags = {"program_id": str(program_id), "FILE_TYPE": "EnrollmentRequestMessage"}
        Note:
            1. ids should be passed as string
            2. FILE_TYPE should be the name of dataclass and passed as string
        """
        number_of_rows = validate_uploaded_csv_and_row_count(file)
        timestamped_filename = generate_safe_unique_file_name(
            file.filename  # type:ignore[arg-type]
        )

        self.put_filehandle(
            file_name=timestamped_filename,
            # self.put_filehandle() throws error at file.get_value()
            # as tempfile doesn't support get_value() method
            # this is fixed in python 3.11
            # check for reference https://docs.python.org/3.11/whatsnew/3.11.html#tempfile
            # remove type ignore with python upgrade to 3.11
            file_data=file,  # type:ignore
            tags={
                "original_file_name": secure_filename(file.filename),  # type:ignore[arg-type]
                "number_of_rows": str(max(0, number_of_rows - 1)),
                **tags,
            },
        )
        logger.info(
            f"File with {timestamped_filename} filename uploaded to"
            f" '{self.bucket_name}' minio bucket"
        )
