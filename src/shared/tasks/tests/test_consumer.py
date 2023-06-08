from unittest.mock import Mock

from confluent_kafka import Message

from shared.minio_manager import FakeMessage
from shared.tasks.consumer import BatchMessageConsumer, SingleMessageConsumer


class TestSingleMessageConsumer:
    def test_execute_consumer(self):
        items = [
            Mock(
                spec=Message,
                headers=lambda: [("program_id", b"123")],
                topic=lambda: "my-topic",
                value=lambda: b'[{"program_id": 1}]',
            ),
            Mock(
                spec=Message,
                headers=lambda: [("program_id", b"456")],
                topic=lambda: "registered-topic-with-no-consumer",
                value=lambda: b'[{"program_id": 2}]',
            ),
        ]

        mock_kafka_consumer = Mock()
        mock_consumer_fn = Mock(schema=FakeMessage.schema(many=True))
        consumer = SingleMessageConsumer(
            consumer=mock_kafka_consumer, topics={"my-topic": [(mock_consumer_fn)]}
        )
        consumer.execute_consumers_on_topic(items[0])
        consumer.execute_consumers_on_topic(items[1])
        mock_consumer_fn.assert_called_once()

    def test_execute_consumer_headers_merged(self):
        # given a list of messages,take the kafka headers and add them to the
        # individual messages
        msg = [
            FakeMessage(program_id=123),
            FakeMessage(program_id=456),
        ]
        mock_kafka_consumer = Mock()
        mock_consumer_fn = Mock()
        mock_consumer_fn.schema = FakeMessage.schema(many=True)
        msg_json = FakeMessage.schema().dumps(msg, many=True)
        kafka_message = Mock(
            spec=Message,
            headers=lambda: [("program_id", b"123")],
            topic=lambda: "fake-topic",
            value=lambda: msg_json.encode("utf-8"),  # byte string
        )

        consumer = SingleMessageConsumer(
            consumer=mock_kafka_consumer, topics={"fake-topic": [(mock_consumer_fn)]}
        )
        consumer.execute_consumers_on_topic(message=kafka_message)
        mock_consumer_fn.assert_called_once()
        mock_consumer_fn.assert_called_with(
            data=[
                FakeMessage(program_id=123),
                FakeMessage(program_id=456),
            ],
            headers={"program_id": "123"},
        )
        assert mock_consumer_fn.call_args.kwargs["data"][0].headers == {"program_id": "123"}
        assert mock_consumer_fn.call_args.kwargs["data"][1].headers == {"program_id": "123"}

    def test_append_batch_header(self):
        messages = [FakeMessage(program_id=123), FakeMessage(program_id=456)]
        messages[0].set_headers({"current": "true"})
        FakeMessage.batch_set_header(messages, {"batch_added": "true"})
        assert messages[0].headers == {
            "batch_added": "true",
            "current": "true",
        }


class TestBatchConsumer:
    def test_execute_consumer(self):
        TOPIC_1 = "my-topic"
        TOPIC_2 = "other-topic"
        items = [
            Mock(
                spec=Message,
                headers=lambda: [("program_id", b"123")],
                topic=lambda: TOPIC_1,
                value=lambda: b'[{"program_id": 1}]',
                error=lambda: None,
            ),
            Mock(
                spec=Message,
                headers=lambda: [("program_id", b"456")],
                topic=lambda: TOPIC_2,
                value=lambda: b'[{"program_id": 2}]',
                error=lambda: None,
            ),
        ]

        mock_kafka_consumer = Mock()
        mock_consumer_fn = Mock()
        mock_consumer_fn_2 = Mock()
        consumer = BatchMessageConsumer(
            consumer=mock_kafka_consumer,
            topics={TOPIC_1: [mock_consumer_fn], TOPIC_2: [mock_consumer_fn_2]},
        )
        consumer.send_messages_to_handler(items)
        mock_consumer_fn.assert_called_once()
        mock_consumer_fn_2.assert_called_once()
