import orjson
import pika
import pytest

from throw_catch import catch, clear, throw


@pytest.fixture
def rabbitmq_connection(mocker):
    connection = mocker.Mock()
    channel = mocker.Mock()
    connection.channel.return_value = channel
    blocking_connection = mocker.patch("pika.BlockingConnection", return_value=connection)
    return blocking_connection, connection, channel


class TestThrow:
    def test_throw_publishes_message_successfully(self, rabbitmq_connection):
        blocking_connection, connection, channel = rabbitmq_connection

        payload = {"key": "value"}
        uri = "amqp://guest:guest@localhost:5672/"

        throw(payload=payload, uri=uri)

        blocking_connection.assert_called_once_with(pika.URLParameters(uri))
        channel.queue_declare.assert_called_once_with(queue="throw_catch", durable=False)
        channel.basic_publish.assert_called_once()
        publish_kwargs = channel.basic_publish.call_args.kwargs
        assert publish_kwargs["exchange"] == ""
        assert publish_kwargs["routing_key"] == "throw_catch"
        assert publish_kwargs["properties"].expiration == "10800000"
        body = orjson.loads(publish_kwargs["body"])
        assert body["payload"] == payload
        assert body["routing_key"] == "throw_catch"
        assert body["ttl"] == 180
        assert body["tag"] is None
        assert body["filename"].endswith("test_throw_catch.py")
        assert body["function_name"] == "test_throw_publishes_message_successfully"
        connection.close.assert_called_once()

    def test_throw_without_ttl_does_not_set_expiration(self, rabbitmq_connection):
        _blocking_connection, connection, channel = rabbitmq_connection

        throw(payload={"key": "value"}, uri="amqp://guest:guest@localhost:5672/", ttl=0)

        publish_kwargs = channel.basic_publish.call_args.kwargs
        assert "properties" not in publish_kwargs
        connection.close.assert_called_once()

    @pytest.mark.parametrize(
        ("payload", "uri", "tag", "routing_key", "ttl", "message"),
        [
            ({}, "amqp://guest:guest@localhost:5672/", None, "throw_catch", 180, "Payload dictionary required"),
            ({"ok": True}, "", None, "throw_catch", 180, "AMQP uri required and must be string"),
            ({"ok": True}, "amqp://guest:guest@localhost:5672/", "тег", "throw_catch", 180, "Invalid tag name"),
            ({"ok": True}, "amqp://guest:guest@localhost:5672/", None, "очередь", 180, "Invalid routing key name"),
            ({"ok": True}, "amqp://guest:guest@localhost:5672/", None, "throw_catch", -1, "TTL message must be positive integer"),
        ],
    )
    def test_throw_validates_inputs(self, payload, uri, tag, routing_key, ttl, message):
        with pytest.raises(AssertionError, match=message):
            throw(payload=payload, uri=uri, tag=tag, routing_key=routing_key, ttl=ttl)

    def test_throw_logs_connection_errors(self, mocker):
        logger = mocker.patch("throw_catch.src.LOGGER")
        mocker.patch("pika.BlockingConnection", side_effect=RuntimeError("boom"))

        throw(payload={"key": "value"}, uri="amqp://guest:guest@localhost:5672/")

        logger.exception.assert_called_once_with("Failed to publish message to RabbitMQ")


class TestCatch:
    def test_catch_retrieves_single_message(self, rabbitmq_connection, mocker):
        _blocking_connection, connection, channel = rabbitmq_connection
        method = mocker.Mock(delivery_tag=1)
        message = {"tag": "test_tag", "data": "test_data"}
        channel.basic_get.return_value = (method, None, orjson.dumps(message))

        result = catch(uri="amqp://test", queue="test_queue")

        assert result == [message]
        channel.queue_declare.assert_called_once_with(queue="test_queue", durable=False)
        channel.basic_get.assert_called_once_with("test_queue")
        channel.basic_ack.assert_called_once_with(1)
        connection.close.assert_called_once()

    def test_catch_stops_when_queue_is_empty(self, rabbitmq_connection):
        _blocking_connection, connection, channel = rabbitmq_connection
        channel.basic_get.return_value = (None, None, None)

        result = catch(uri="amqp://test", queue="test_queue", count=5)

        assert result == []
        channel.basic_get.assert_called_once_with("test_queue")
        channel.basic_ack.assert_not_called()
        connection.close.assert_called_once()

    def test_catch_filters_by_tag(self, rabbitmq_connection, mocker):
        _blocking_connection, connection, channel = rabbitmq_connection
        first_method = mocker.Mock(delivery_tag=1)
        second_method = mocker.Mock(delivery_tag=2)
        channel.basic_get.side_effect = [
            (first_method, None, orjson.dumps({"tag": "skip", "payload": 1})),
            (second_method, None, orjson.dumps({"tag": "keep", "payload": 2})),
        ]

        result = catch(uri="amqp://test", queue="test_queue", count=2, tag="keep")

        assert result == [{"tag": "keep", "payload": 2}]
        channel.basic_ack.assert_called_once_with(2)
        connection.close.assert_called_once()

    @pytest.mark.parametrize(
        ("uri", "queue", "count", "tag", "message"),
        [
            ("", "test_queue", 1, None, "AMQP uri required and must be string"),
            ("amqp://test", "очередь", 1, None, "Invalid queue name"),
            ("amqp://test", "test_queue", 0, None, "Count must be positive integer"),
            ("amqp://test", "test_queue", 1, "тег", "Invalid tag name"),
        ],
    )
    def test_catch_validates_inputs(self, uri, queue, count, tag, message):
        with pytest.raises(AssertionError, match=message):
            catch(uri=uri, queue=queue, count=count, tag=tag)


class TestClear:
    def test_clear_deletes_queue(self, rabbitmq_connection):
        blocking_connection, connection, channel = rabbitmq_connection
        uri = "amqp://guest:guest@localhost:5672/"

        clear(uri=uri)

        blocking_connection.assert_called_once_with(pika.URLParameters(uri))
        channel.queue_declare.assert_called_once_with(queue="throw_catch", durable=False)
        channel.queue_delete.assert_called_once_with(queue="throw_catch")
        connection.close.assert_called_once()

    @pytest.mark.parametrize(
        ("uri", "queue", "message"),
        [
            ("", "throw_catch", "AMQP uri required and must be string"),
            ("amqp://guest:guest@localhost:5672/", "очередь", "Invalid queue name"),
        ],
    )
    def test_clear_validates_inputs(self, uri, queue, message):
        with pytest.raises(AssertionError, match=message):
            clear(uri=uri, queue=queue)
