import marshmallow as ma

from shared.tasks import decorators


class FakeSchema(ma.Schema):
    pass


def test_register_topic_handler():
    # Test that the decorator adds the correct attributes to the decorated function
    TOPIC = "my-topic"

    @decorators.register_topic_handler(TOPIC, FakeSchema)
    def my_handler(data):
        pass

    assert my_handler.schema == FakeSchema
    assert TOPIC in decorators.registered_topic_handlers
    assert my_handler in decorators.registered_topic_handlers[TOPIC]
