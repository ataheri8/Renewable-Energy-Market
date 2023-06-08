# TODO - this test is not working.
# flake8: noqa
# type: ignore

import io
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from time import sleep
from unittest import mock
from unittest.mock import ANY, Mock, patch

import pytest
from faker import Faker
from marshmallow import ValidationError
from minio import Minio
from minio.helpers import ObjectWriteResult

from pm.bucket_watcher import MinioManager, send_batches_to_kafka
from pm.data_transfer_objects.csv_upload_kafka_messages import (
    EnrollmentRequestMessage,
    ServiceProviderDERAssociateMessage,
    ServiceProviderMessage,
)
from pm.modules.enrollment.models import *  # noqa
from pm.modules.progmgmt.models import *  # noqa
from pm.modules.serviceprovider.models import *  # noqa
from shared.minio_manager import FakeMessage, Message, Notification
from shared.tools.utils import generate_safe_unique_file_name

# fyi minio is strict about what characters are allowed in bucket names: eg: no underscores
TEST_BUCKET_PREFIX = "test"


@pytest.fixture()
def tear_down_buckets():
    yield
    print("delete test buckets after running tests")
    nuke_buckets()


@pytest.fixture
def filemanager_client():
    """Create a minio client"""
    # see minio console at http://localhost:9001/login
    # user/pw : gridosgridos / gridosgridos
    # or get credentials from docker-compose.yml
    return _get_client()


@pytest.fixture
def miniomanager_client():
    """Create a minio client"""
    # see minio console at http://localhost:9001/login
    # user/pw : gridosgridos / gridosgridos
    # or get credentials from docker-compose.yml
    return MinioManager(bucket_name="test")


def _get_client():
    return  # LocalFileManger()


@pytest.fixture
def nuke_all_test_buckets(test_bucket_prefix=TEST_BUCKET_PREFIX):
    nuke_buckets(test_bucket_prefix)


def nuke_buckets(test_bucket_prefix=TEST_BUCKET_PREFIX):
    # if a bucket is prefixed 'test_' then delete it
    client = _get_client()
    buckets = client.list_buckets()
    test_buckets = [bucket for bucket in buckets if bucket.startswith(test_bucket_prefix)]
    for bucket in test_buckets:
        try:
            objects = client.list_files(bucket)
        except NotADirectoryError:
            continue
        for obj in objects:
            client.bucket_name = bucket
            client.delete_file(obj)
        client.delete_bucket(bucket)


@pytest.fixture
def generate_test_label():
    return test_label_generator()


def test_label_generator():
    return f"{TEST_BUCKET_PREFIX}{Faker().word()}"


@pytest.mark.skip(reason="Requires Minio to be running.")
class TestFileHandler:
    # see minio console at http://localhost:9001/login
    # user/pw : gridosgridos / gridosgridos
    # see credentials from docker-compose.yml

    def test_minio_nuke_test_buckets(self, nuke_all_test_buckets, filemanager_client):
        buckets = [b for b in filemanager_client.list_buckets() if b.startswith(TEST_BUCKET_PREFIX)]
        assert len(buckets) == 0

    def test_minio_create_test_buckets(
        self, nuke_all_test_buckets, filemanager_client, generate_test_label, tear_down_buckets
    ):
        prior_buckets = filemanager_client.list_buckets()
        filemanager_client.create_bucket(generate_test_label)
        sleep(0.1)
        current_buckets = filemanager_client.list_buckets()
        assert len(current_buckets) == len(prior_buckets) + 1

    def test_delete_bucket(self, nuke_all_test_buckets, filemanager_client, generate_test_label):
        bucket_name = generate_test_label
        filemanager_client.create_bucket(bucket_name)
        buckets = filemanager_client.list_buckets()
        prior_count = len(buckets)
        filemanager_client.delete_bucket(bucket_name)
        buckets = filemanager_client.list_buckets()
        assert len(buckets) == prior_count - 1

    def test_put_bytes_and_get_bytes_from_minio(
        self, nuke_all_test_buckets, filemanager_client, generate_test_label, tear_down_buckets
    ):
        filemanager_client.create_bucket(generate_test_label)
        filemanager_client.bucket_name = generate_test_label
        file_handle = io.BytesIO(b"test" + bytes(generate_test_label, "utf-8"))
        results: ObjectWriteResult = filemanager_client.put_filehandle(
            file_name=generate_test_label,
            file_data=file_handle,
        )
        assert type(filemanager_client.get_string_io(generate_test_label)) == StringIO
        assert results.bucket_name == generate_test_label
        assert results.object_name == generate_test_label

    def test_move_file(self, filemanager_client, generate_test_label, tear_down_buckets):
        filemanager_client.create_bucket(generate_test_label)
        filemanager_client.bucket_name = generate_test_label
        filemanager_client.put_filehandle(file_name="test.txt", file_data=(io.BytesIO(b"test")))
        dest_folder = test_label_generator()
        filemanager_client.create_bucket(dest_folder)
        filemanager_client.move_file(
            source_bucket=generate_test_label,
            source_filename="test.txt",
            destination_bucket=dest_folder,
            destination_filename="test.txt",
        )
        print("from", generate_test_label, "to", dest_folder)
        assert len(filemanager_client.list_files(generate_test_label)) == 0
        assert len(filemanager_client.list_files(dest_folder)) == 1

    def test_save_csv_as_file(self, generate_test_label, filemanager_client, tear_down_buckets):
        filemanager_client.bucket_name = generate_test_label
        filemanager_client.create_bucket(generate_test_label)
        # we can run test from the test folder or from root folder: so we
        # should be able to find the test file in either case
        current_dir = Path().absolute()
        file_path = (
            current_dir / "der_sample.csv"
            if "tests" in str(current_dir)
            else current_dir / "tests" / "tasks_test" / "der_sample.csv"
        )
        filemanager_client.put_file(file_path=str(file_path))
        assert len(filemanager_client.list_files(bucket_name=generate_test_label)) == 1
        #         we should also have an enrollment record too - but that's a manual check for now

    def test_list_bucket(
        self, nuke_all_test_buckets, filemanager_client, generate_test_label, tear_down_buckets
    ):
        bucket_name = generate_test_label
        filemanager_client.create_bucket(bucket_name)
        buckets = filemanager_client.list_buckets()
        assert bucket_name in str(buckets)

    def test_put_filehandle(self, nuke_all_test_buckets, filemanager_client, generate_test_label):
        with patch(
            "shared.file_manager.open",
            create=True,
        ) as mock_file:
            filemanager_client.put_filehandle(
                file_name=generate_test_label,
                file_data=io.BytesIO(b"test"),
            )
            mock_file.assert_called_once_with(
                ANY, "wb"
            )  # mock_file.write.assert_called_with(contents)
            mock_file.assert_called_once_with(
                filemanager_client._get_filepath(
                    source_bucket=filemanager_client.bucket_name,
                    source_filename=generate_test_label,
                ),
                "wb",
            )

    def test_list_files(self, nuke_all_test_buckets, filemanager_client, generate_test_label):
        with patch(
            "shared.file_manager.os.listdir",
        ) as mock_listdir:
            filemanager_client.list_files(generate_test_label)
            assert generate_test_label in str(mock_listdir.call_args)


@pytest.mark.skip(reason="Requires Minio to be running.")
class TestMinioManager:
    def test_make_minio_bucket(
        self,
        miniomanager_client,
        generate_test_label,
    ):
        with patch.object(
            Minio,
            "make_bucket",
        ) as mock_minio:
            miniomanager_client.create_bucket(generate_test_label)
            mock_minio.assert_called_once()

    def test_delete_minio_bucket(self, miniomanager_client, generate_test_label):
        with patch.object(
            Minio,
            "remove_bucket",
        ) as mock_minio:
            miniomanager_client.delete_bucket(bucket_name=generate_test_label)
            mock_minio.assert_called_once()

    def test_list_minio_buckets(self, miniomanager_client, generate_test_label):
        # create a fake object
        x = Mock()
        x.name = generate_test_label
        with patch.object(Minio, "list_buckets", return_value=[x]) as mock_minio:
            result = miniomanager_client.list_buckets()
            mock_minio.assert_called_once()
            assert result == [generate_test_label]

    def test_get_string_io(self, miniomanager_client, generate_test_label):
        x = Mock()
        x.data = b"test_file_data"
        with patch.object(Minio, "get_object", return_value=x) as mock_minio:
            result = miniomanager_client.get_string_io(file_name=generate_test_label)
            mock_minio.assert_called_once()
            assert result.read() == "test_file_data"

    def test_put_filehandle(self, miniomanager_client, generate_test_label):
        with patch.object(Minio, "put_object") as mock_minio:
            file_data = io.BytesIO(b"test")
            miniomanager_client.put_filehandle(
                file_name=generate_test_label,
                file_data=file_data,
            )
            mock_minio.assert_called_once()
            # we have to use 'any' for the data because it's a file handle-
            # for each use,the pointer is different
            mock_minio.assert_called_with(
                bucket_name=miniomanager_client.bucket_name,
                object_name=generate_test_label,
                data=ANY,
                length=4,
                tags={"FILE_TYPE": "OTHER"},
            )

    def test_append_tags(self, miniomanager_client, generate_test_label):
        file_data = io.BytesIO(b"test")
        m = MinioManager()
        txt = generate_safe_unique_file_name("test.txt")
        m.put_filehandle(
            file_name=txt,
            file_data=file_data,
            tags={"FILE_TYPE": "DER"},
        )
        m.add_tags(file_name=txt, new_tags={"new_tag": "new_tag_value"})
        tags = m.get_tags(file_name=txt)
        assert tags["FILE_TYPE"] == "DER"
        assert tags["new_tag"] == "new_tag_value"

    def test_put_file(self, miniomanager_client, generate_test_label):
        with patch.object(Minio, "fput_object") as mock_minio:
            file_path = "/path/to/the/file/" + generate_test_label
            miniomanager_client.put_file(file_path=file_path, csv_type=CSVType.DER)
            mock_minio.assert_called_once()
            mock_minio.assert_called_with(
                bucket_name=miniomanager_client.bucket_name,
                object_name=generate_test_label,
                file_path=file_path,
                tags={"FILE_TYPE": "DER"},
            )

    def test_generate_list_files(self, miniomanager_client, generate_test_label):
        x = Mock()
        x.object_name = "new_file"
        with patch.object(Minio, "list_objects", return_value=[x]) as mock_minio:
            result = miniomanager_client.generate_list_file_names(
                bucket_name=generate_test_label
            ).__next__()
            mock_minio.assert_called_once()
            mock_minio.assert_called_with(bucket_name=generate_test_label)
            assert result == "new_file"

    def test_move_files(self, miniomanager_client, generate_test_label):
        with patch.object(Minio, "remove_object") as mock_minio_remove:
            with patch.object(Minio, "copy_object") as mock_minio_copy:
                miniomanager_client.move_file(
                    source_bucket=generate_test_label,
                    source_filename=generate_test_label,
                    destination_bucket="dest_bucket",
                    destination_filename="dest_file",
                )

            mock_minio_copy.assert_called_once()
            mock_minio_copy.assert_called_with(
                bucket_name="dest_bucket", object_name="dest_file", source=ANY
            )
            mock_minio_remove.assert_called_once()
            mock_minio_remove.assert_called_with(
                bucket_name=generate_test_label, object_name=generate_test_label
            )

    def test_upload_with_no_file_type_exception_raised(
        self, miniomanager_client, generate_test_label
    ):
        miniomanager_client.ensure_bucket_exists(bucket_name="test")
        file_path = "der_sample.csv"
        miniomanager_client.put_file(file_path=file_path)
        files = miniomanager_client.list_files()
        assert files


class TestMessageClasses:
    def test_message_classes_needs_Metaclass(self):
        with pytest.raises(ValidationError):

            @dataclass
            class SimpleMessage(Message):
                message: str

            SimpleMessage(message="test")

    def test_message_classes_Metaclass_is_correct(self):
        @dataclass
        class SimpleMessage(Message):
            message: str

            class Meta:
                topic = "test_topic"

            def process_message(self):
                pass

        message = SimpleMessage(message="test")
        assert message.message == "test"
        assert message.Meta.topic == "test_topic"
        assert message.headers == {}

    def test_message_classes_Metaclass_headers(self):
        @dataclass
        class SimpleMessage(Message):
            message: str

            class Meta:
                topic = "test_topic"
                headers = {"test": "test"}

            def process_message(self):
                pass

        message = SimpleMessage(message="test")
        assert message.message == "test"
        assert message.Meta.headers == {"test": "test"}
        assert message.Meta.topic

    def test_message_classes_Metaclass_headers_omitted(self):
        @dataclass
        class SimpleMessage(Message):
            message: str

            class Meta:
                topic = "test_topic"

            def process_message(self):
                pass

        message = SimpleMessage(message="test")
        assert message.message == "test"
        assert message.headers == {}
        assert message.Meta.topic

    def test_message_classes_Metaclass_batchsize_implicit(self):
        @dataclass
        class SimpleMessage(Message):
            message: str

            class Meta:
                topic = "test_topic"

            def process_message(self):
                pass

        message = SimpleMessage(message="test")
        assert message.message == "test"
        assert message.headers == {}
        assert message.Meta.batch_size == 50
        assert message.Meta.topic

    def test_message_classes_Metaclass_custom_batchsize(self):
        @dataclass
        class SimpleMessage(Message):
            message: str

            class Meta:
                topic = "test_topic"
                batch_size = 100

            def process_message(self):
                pass

        message = SimpleMessage(message="test")
        assert message.message == "test"
        assert message.headers == {}
        assert message.Meta.batch_size == 100
        assert message.Meta.topic


class TestNotifications:
    def test_create_notification(self):
        notification = Notification(
            session_id=123,
            additional_data={"test": "test"},
        )
        assert notification.notification_type == "Update"

    def test_process_message_send_notification(self):
        with patch.object(Notification, "send_to_kafka") as mock_send_notification:
            sent_notification = FakeMessage.send_progress_notification(
                batch_number=1,
                tags={
                    "session_id": 12234,
                    "test": "test_process_message_send_notification",
                },
            )
        assert sent_notification.notification_type == "progress"
        assert sent_notification.additional_data["test"] == "test_process_message_send_notification"
        assert sent_notification.additional_data["topic"] == "fakeTopic"
        assert sent_notification.session_id == 12234

    def test_notification_headers(self):
        fakemsg = FakeMessage(
            program_id=123,
        )
        fakemsg.set_headers(
            {
                "session_id": 123,
                "test_header": "test123",
            }
        )
        with patch.object(Notification, "send_to_kafka") as mock_send_notification:
            sent_notification = FakeMessage.send_progress_notification(
                batch_number=1,
                tags={
                    "session_id": 12234,
                    "test": "test_process_message_send_notification",
                },
            )
        assert sent_notification.additional_data == {
            "session_id": 12234,
            "test": "test_process_message_send_notification",
            "topic": "fakeTopic",
            "batch_size": 50,
            "batch_number": 1,
            "row_number": 100,
        }
        assert sent_notification.headers == {
            "session_id": 12234,
            "test": "test_process_message_send_notification",
            "topic": "fakeTopic",
            "batch_size": 50,
            "batch_number": 1,
            "row_number": 100,
        }

    def test_headers(self):
        f1 = FakeMessage(program_id=123)
        f1.set_headers({"test_header": "test123"})
        assert f1.headers == {"test_header": "test123"}
        r = f1.schema().loads('{"program_id": 123}')
        assert r == f1

    def test_listen_to_bucket_process_rows_creates_notification(self):
        with mock.patch.object(FakeMessage, "_send_notification") as mock_notification:
            processed = send_batches_to_kafka(
                message_class=FakeMessage,
                row_generator=[{"program_id": 234}],
                tags={"user_id": "test_user_id"},
            )
            assert processed
        assert mock_notification.called

    # def test_bucket_watcher_creates_error_notification(self):
    #     with mock.patch.object(FakeMessage, "_send_notification") as mock_notification:
    #         processed = send_batches_to_kafka(
    #             message_class=FakeMessage,
    #             row_generator=[{"program_id": "abc"}],
    #             tags={"user_id": "test_user_id"},
    #         )
    #         assert not processed
    #     assert mock_notification.call_count == 2
    #     assert mock_notification.call_args_list[0][0][0] == "error"
    #     assert mock_notification.call_args_list[1][0][0] == "progress"

    def test_notification_content(self):
        with mock.patch.object(Notification, "send_to_kafka") as mock_notification_send:
            processed = send_batches_to_kafka(
                message_class=FakeMessage,
                row_generator=[{"program_id": 234}],
                tags={"user_id": "test_user_id", "session_id": "test_session_id"},
            )
            assert processed
        assert mock_notification_send.called

    def test_error_row_behaviour(self):
        batch_number = 1
        tags = {}
        row_batch = [
            {"program_id": "abd"},
            {"program_id": 234},
        ]
        batch_data = [
            FakeMessage.message_factory(
                row,
                row_number,
                batch_number,
                tags,
            )
            for row_number, row in enumerate(row_batch)
        ]
        print(batch_data)
        assert batch_data

    def test_empty_list_schema_convert(self):
        list_of_messages = []
        objs = FakeMessage.schema().dumps(list_of_messages, many=True)
        assert objs == "[]"

    def test_tags_in_headers(self):
        f1 = FakeMessage.message_factory(
            row={"program_id": 123},
            row_number=1,
            batch_number=0,
            tags={"test": "test"},
        )
        assert f1.headers == {
            "test": "test",
            "topic": "fakeTopic",
            "batch_size": 50,
            "batch_number": 0,
            "row_number": 1,
        }


class TestCSVGeneration:
    @pytest.mark.parametrize(
        "class_name, headers",
        [
            pytest.param(
                EnrollmentRequestMessage,
                "DER_ID,Import Target capacity (kW) (optional),Export Target Capacity (kW)"
                " (optional),Default Limits - Active Power Import (kW) (optional),"
                "Default Limits - Active Power Export (kW) (optional),Default Limits - "
                "Reactive Power Import (kW) (optional),Default Limits - Reactive Power "
                "Export (kW) (optional)\r\n",
            ),
            pytest.param(
                ServiceProviderMessage,
                "Name,Type,Primary contact,Primary email,Notification contact,Notification email,"
                "Street Address,Apt/unit,City,State/Province/Region,Country,ZIP/Postal Code,Status"
                "\r\n",
            ),
            pytest.param(ServiceProviderDERAssociateMessage, "der_id\r\n"),
        ],
    )
    def test_generate_csv(self, class_name: Message, headers):
        output = class_name.generate_csv_template()
        assert output.read().decode("utf-8-sig") == headers
