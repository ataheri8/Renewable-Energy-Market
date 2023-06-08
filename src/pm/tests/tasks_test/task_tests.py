# TODO - this test is not working.
# flake8: noqa
# type: ignore

import csv
import io
import random
from collections import namedtuple
from time import sleep
from unittest.mock import patch
from uuid import uuid4

import pytest
from confluent_kafka import Consumer as KafkaConsumer
from dotenv import load_dotenv
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from pm.bucket_watcher import (
    ExtractCSVrows,
    listen_to_bucket_process_rows,
    main_file_watcher,
)
from pm.config import PMConfig
from pm.consumers.event.handle_service_provider_der_association_message import (
    handle_service_provider_der_message,
)
from pm.data_transfer_objects.csv_upload_kafka_messages import (
    ServiceProviderDERAssociateMessage,
)
from pm.modules.enrollment.controller import EnrollmentController
from pm.modules.enrollment.enums import EnrollmentRequestStatus
from pm.modules.enrollment.services.enrollment import EnrollmentRequestGenericFieldsDict
from pm.tests.factories import DerFactory, ProgramFactory, ServiceProviderFactory
from shared.minio_manager import Message, MinioManager
from shared.system import configuration
from shared.tasks.producer import MessageData
from shared.tools.utils import generate_safe_unique_file_name, generate_timestamp

FAKE_ENROLLMENT_DATA = EnrollmentRequestGenericFieldsDict(
    **{
        "program_id": "123",
        "enrollment_status": "ACCEPTED",
        "service_provider": "service_provider",
        "der_id": "der_id",
    }
)


@pytest.fixture
def fake_enrollment_data() -> EnrollmentRequestGenericFieldsDict:
    return fake_enrollment_data_factory()


def fake_enrollment_data_factory() -> EnrollmentRequestGenericFieldsDict:
    id_1 = random.randint(0, 10000000)
    id_2 = random.randint(0, 10000000)
    id_3 = random.randint(0, 10000000)
    der_uuid = f"{uuid4()}"
    try:
        ProgramFactory(id=id_1)
    except SQLAlchemyError as err:
        print(f"err {err}  - program with id {id_1} already exists, continuing..")
    try:
        ServiceProviderFactory(id=id_2)
    except SQLAlchemyError as err:
        print(f"err {err}  - service_provider with id {id_2} already exists, continuing..")
    try:
        DerFactory(id=id_3, der_id=der_uuid, service_provider_id=id_2)
    except SQLAlchemyError as err:
        print(f"err {err}  - der with id {id_3} already exists, continuing..")
    data = EnrollmentRequestGenericFieldsDict(
        **{
            "program_id": id_1,
            "enrollment_status": random.choice(list(EnrollmentRequestStatus)),
            "service_provider_id": id_2,
            "der_id": der_uuid,
        }
    )
    return data


def create_fake_csv_file(fp="fake_data.csv"):
    # convenience method for manual testing!
    with open(fp, "w", newline="") as csvfile:
        fieldnames = FAKE_ENROLLMENT_DATA.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({**FAKE_ENROLLMENT_DATA})
        writer.writerow({**FAKE_ENROLLMENT_DATA})
    return fp


class TestWriteConsumer:
    @pytest.mark.skip(reason="This test is end-to-end and requires some setup - see docstring")
    def test_end_to_end(self, client, db_session):
        # this test assumes that the kafka broker, minio, minio_watcher & kafka consumer scripts are running
        # also assumes the .env file has DB_NAME=test - so the scripts are using the same db as the tests
        # ie: run poetry run invoke stack-up
        # ie: run poetry run bucket_watcher.py
        # ie: run poetry run flask app .py
        prior_enrollment_count = len(EnrollmentController().get_all_enrollment_requests())
        rand_program_id = str(random.randint(0, 10000000))
        try:
            ProgramFactory(id=rand_program_id)
        except SQLAlchemyError as e:
            print(f"ProgramFactory already exists? : {e}")
        minio_manager = MinioManager(bucket_name="target")
        new_csv_file_name = f"der_sample_{rand_program_id}.csv"
        with open("der_sample.csv", "rb") as f:
            file_content = f.read()
            # swap out placeholder program ID
            file_content = file_content.replace(b"123", rand_program_id.encode("utf-8"))
            minio_manager.put_filehandle(
                file_name=new_csv_file_name, file_data=io.BytesIO(file_content)
            )
        # wait for the consumer to process the file
        sleep(0.75)
        db_session.commit()
        assert (
            len(EnrollmentController().get_all_enrollment_requests()) == prior_enrollment_count + 1
        )
        assert new_csv_file_name not in minio_manager.list_files(bucket_name="target")
        assert new_csv_file_name in minio_manager.list_files(
            bucket_name=configuration.get_config().MINIO_PROCESSED_FOLDER
        )

    def test_extract_csv_rows(self):
        def side_effect_get_string_io_as_get_file(csv_file):
            return open(csv_file, "r", encoding="utf-8")

        with patch.object(MinioManager, "get_file_type", return_value=CSVType.OTHER):
            with patch.object(
                MinioManager, "get_string_io", side_effect=side_effect_get_string_io_as_get_file
            ):
                with ExtractCSVrows(
                    file_name="der_sample.csv", path="source", error_bucket="error"
                ) as rows:
                    for row in rows:
                        assert row["program_id"] == "123"
                        assert row["enrollment_program_type"] == "GENERIC"
                    assert len([rows]) == 1

    def test_extract_non_csv_and_move_file(self):
        def side_effect_get_string_io_fail(csv_file):
            raise UnicodeDecodeError("not a csv file", b"not a csv file", 0, 0, "not a csv file")

        with patch.object(MinioManager, "move_file") as move_file:
            with patch.object(
                MinioManager, "get_string_io", side_effect=side_effect_get_string_io_fail
            ):
                with ExtractCSVrows(
                    file_name="kitten.png", path="source", error_bucket="error"
                ) as rows:
                    assert list(rows) == []
            assert move_file.called
            move_file.assert_called_with(
                source_bucket="source",
                source_filename="kitten.png",
                destination_bucket="error",
                destination_filename="kitten.png",
            )

    def test_listen_to_bucket_process_rows(self):
        csv_data = """program_id,enrollment_program_type,other
1,2,3"""
        with patch("pm.file_repo.sent_row_to_kafka_and_move_file") as mock_send:
            with patch("pm.file_repo.MinioManager") as mock_minio_manager:
                instance = mock_minio_manager.return_value
                instance.get_string_io.return_value = io.StringIO(csv_data)
                instance.listen_bucket_notification.return_value = ["fakefile.csv"]
                instance.generate_list_file_names.return_value = []
                listen_to_bucket_process_rows()
            assert mock_send.called
            mock_minio_manager().move_file.assert_called_once_with(
                source_bucket="target",
                source_filename="fakefile.csv",
                destination_bucket="processed",
                destination_filename="fakefile.csv",
            )
            mock_send.assert_called_with(
                {"program_id": "1", "enrollment_program_type": "2", "other": "3"}
            )

    def test_end_to_end_mocked(self, client, db_session):
        def fake_kafka_message(*args, **kwargs):
            global message_count
            message_count += 1
            if message_count > 1:
                raise StopIteration()
            Message = namedtuple("Message", "id value")
            row = {
                "program_id": "123",
                "enrollment_program_type": "GENERIC",
                "enrollment_status": "ACCEPTED",
                "enrollment_contract_type": "enrollment_contract_type",
                "service_provider": "service_provider",
                "der_id": "der_id",
                "contract_status": "ACTIVE",
            }
            return Message(1, row)

        csv_data = open("der_sample.csv").read()
        global message_count
        message_count = 0
        with patch.object(KafkaConsumer, "__next__", side_effect=fake_kafka_message):
            with patch("pm.file_repo.KafkaProducer.send"):
                with patch("pm.file_repo.sent_row_to_kafka_and_move_file"):
                    with patch("pm.file_repo.MinioManager") as mock_minio_manager:
                        instance = mock_minio_manager.return_value
                        instance.get_string_io.return_value = io.StringIO(csv_data)
                        instance.listen_bucket_notification.return_value = ["fakefile.csv"]
                        instance.generate_list_file_names.return_value = []
                        # ok now we're all mocked and set-up; let's do the same as the manual test above
                        # prior_enrollment_count = len(EnrollmentController().get_all_enrollments())
                        ProgramFactory(id=123)
                        with open("der_sample.csv", "rb") as f:
                            file_content = f.read()
                            MinioManager(bucket_name="target").put_filehandle(
                                file_name=f"der_sample.csv", file_data=io.BytesIO(file_content)
                            )
                        # this function is running independently - but we run it here to test it
                        main_file_watcher()
                        # now we check that the enrollment was created
                        # todo
                        # handle_enrollment_create_control(enrollment=)
                        # assert len(EnrollmentController().get_all_enrollments()) == prior_enrollment_count + 1

    def test_header_setting(self):
        fake1 = FakeMessage(program_id=123)
        fake1.set_headers({"test": "test"})
        assert fake1.program_id == 123
        assert fake1.headers == {"test": "test"}
        fake2 = FakeMessage(program_id=234)
        assert fake2.headers == {}
        fake2.set_headers({"test2": "test2"})
        assert fake2.headers == {"test2": "test2"}
        assert fake1.headers == {"test": "test"}

    def test_extract_csv_rows_with_type(self):
        def side_effect_get_string_io_as_get_file(csv_file):
            return open(csv_file, "r", encoding="utf-8")

        with patch.object(
            MinioManager, "get_string_io", side_effect=side_effect_get_string_io_as_get_file
        ):
            csv_rows_extractor = ExtractCSVrows(
                file_name="der_sample.csv", path="test", error_bucket="error"
            )
            with csv_rows_extractor as rows:
                for row in rows:
                    assert row["program_id"] == "123"
                    assert row["enrollment_program_type"] == "GENERIC"
                    assert csv_rows_extractor.file_type == CSVType.DER
            assert len([rows]) == 1


class TestRenameFilesOnMinioProcessing:
    def test_append_timestamp_to_file(self):
        new_fn = generate_safe_unique_file_name(
            "der_sample.csv", timestamp_generation_function=lambda: "2022-01-01T00:00:00"
        )
        assert new_fn == "der_sample.2022-01-01T00:00:00.csv"

    def test_append_timestamp_to_file_multi_dot(self):
        new_fn = generate_safe_unique_file_name(
            "der.sample.csv", timestamp_generation_function=lambda: "2022-01-01T00:00:00"
        )
        assert new_fn == "der.sample.2022-01-01T00:00:00.csv"
        new_fn = generate_safe_unique_file_name(
            "der.sample.foo.bar.csv", timestamp_generation_function=lambda: "2022-01-01T00:00:00"
        )
        assert new_fn == "der.sample.foo.bar.2022-01-01T00:00:00.csv"

    def test_append_timestamp_to_file_no_dot(self):
        new_fn = generate_safe_unique_file_name(
            "dersample", timestamp_generation_function=lambda: "2022-01-01T00:00:00"
        )
        assert new_fn == "dersample.2022-01-01T00:00:00"

    def test_append_timestamp_to_file_is_wrongtype(self):
        new_fn = generate_safe_unique_file_name(["dersample.csv"], timestamp_generation_function=lambda: "2022-01-01T00:00:00")  # type: ignore
        assert new_fn == "dersample.2022-01-01T00:00:00"

    def test_timestamp_generator_is_unique(self):
        append1 = generate_timestamp()
        sleep(0.0001)
        append2 = generate_timestamp()
        assert type(append1) == str
        assert type(append2) == str
        assert append1 != append2


class TestServiceProviderUpload:
    def test_validate_initial_data(self):
        #     given a dict of service provider data
        from faker import Faker

        fake = Faker()
        current_fake_der = fake.uuid4()

        sample_service = {"der": current_fake_der}
        #     validate it
        service_provider_type = CSVType.SERVICE_PROVIDER
        schema = service_provider_type.get_schema()
        data: MessageData = schema.load(sample_service)
        assert data

    def test_validate_initial_data_with_capitals_fails(self):
        #     given a dict of service provider data
        from faker import Faker

        fake = Faker()
        current_fake_der = fake.uuid4()
        sample_service = {"DER": current_fake_der}
        #     validate it
        service_provider_type = CSVType.SERVICE_PROVIDER
        schema = service_provider_type.get_schema()
        with pytest.raises(ValidationError):
            data: MessageData = schema.load(sample_service)
            assert data

    def test_validate_initial_data_with_wrong_type(self):
        bad_fake_der = "not an actual DER!"
        sample_service = {"der": bad_fake_der}
        #     validate it
        service_provider_type = CSVType.SERVICE_PROVIDER
        schema = service_provider_type.get_schema()
        with pytest.raises(ValidationError):
            data: MessageData = schema.load(sample_service)

    def test_uuid_validation(self):
        pass
        #     validate it
        from uuid import UUID

        for target_bad in [
            "gak",
            "",
            123,
            "123",
            "1234",
            "1234-1234-1234",
            -123,
            123.0,
            b"blah",
            "1234-1234-1234-1234-1234",
        ]:
            with pytest.raises(ValidationError):
                try:
                    result = UUID(target_bad, version=4)
                except (AttributeError, TypeError, ValueError) as ve:
                    print(ve)
                    raise (ValidationError("Invalid UUID"))

        target_good = "c9bf9e57-1685-4c89-bafb-ff5af830be8a"
        result = UUID(target_good, version=4)
        assert result

    def test_uuid_validation_from_dataclass(self):
        service_provider_type = CSVType.SERVICE_PROVIDER
        schema = service_provider_type.get_schema()
        for target_bad in [
            "gak",
            "",
            123,
            "123",
            "1234",
            "1234-1234-1234",
            -123,
            123.0,
            b"blah",
            "1234-1234-1234-1234-1234",
        ]:
            with pytest.raises(ValidationError):
                data = schema.load({"der": target_bad})


class TestServiceProviderConsumer:
    def test_get_message_from_kafka_topic_and_process_it(self):
        #     given a dict of service provider data
        message_from_kafka = [
            {
                "der": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
            }
        ]
        # call the consumer function with the message
        r = handle_service_provider_der_message(message_from_kafka)
        # count_ders again
        assert r


class Test_bucket_processor:
    def test_process_files(self):
        load_dotenv()
        configuration.init_config(PMConfig)
        # listen_to_bucket_process_rows(file_manager=LocalFileManger())

        listen_to_bucket_process_rows()

    def test_validate_invalid_service_provider_der_associate_message(self):
        with pytest.raises(ValidationError):
            ServiceProviderDERAssociateMessage(
                der_rdf_id="c9bf9e57-1685-4c89-bafb-ff5af830be8a",
                asset_type="NOT_A_REAL_ASSET_TYPE",
                limit_unit_type="NOT_A_REAL_LIMIT_UNIT_TYPE",
            )

    def test_validate_service_provider_der_associate_message(self):
        for asset_type in ["DR", "BESS", "EV_CHRG_STN", "PV", "WIND_FARM", "SYNC_GEN", "OTHER"]:
            ServiceProviderDERAssociateMessage(
                der_rdf_id="c9bf9e57-1685-4c89-bafb-ff5af830be8a",
                asset_type=asset_type,
                limit_unit_type="NOT_A_REAL_LIMIT_UNIT_TYPE",
            )

    def test_file_has_no_tags(self):
        m = MinioManager(bucket_name="target")
        m.get_file_type_tag("sample.csv")

    def test_put_fake(self):
        file_content = b"program_id,\n1\n2\nabc"
        MinioManager(bucket_name="target").put_filehandle(
            file_name=f"sample.csv",
            tag={"FILE_TYPE": "fakeMessage"},
            file_data=io.BytesIO(
                file_content,
            ),
        )


class TestDTOSubclasses:
    @pytest.mark.parametrize(
        "subclass",
        [
            "FakeMessage",
            "Notification",
            "EnrollmentMessage",
            "EnrollmentRequestMessage",
            "ServiceProviderDERAssociateMessage",
            "ServiceProviderMessage",
        ],
    )
    def test_subclass_found(self, subclass):
        """
        Testing cls.__subclassess__() dunder method not including subclass from different modules
        """
        subclass = Message.get_matching_class_label(subclass)
        assert subclass


class TestMinioManager:
    def test_error(self):
        with pytest.raises(Exception):
            fc = io.BytesIO(b"test")
            m = MinioManager(
                bucket_name="target",
                end_point="bad",
                secret_key="bad",
                access_key="bad",
            )
            m.put_filehandle(
                file_name="test123",
                file_data=fc,
                tags={"good": "stuff"},
            )
