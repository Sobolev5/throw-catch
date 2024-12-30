import pika
import pytest
import orjson
from throw_catch import throw, catch, clear



class TestThrow:

    def test_throw_publishes_message_successfully(self, mocker):
        mock_connection = mocker.Mock()
        mock_channel = mocker.Mock()
        mock_connection.channel.return_value = mock_channel
    
        mock_blocking_connection = mocker.patch('pika.BlockingConnection')
        mock_blocking_connection.return_value = mock_connection
    
        payload = {"key": "value"}
        uri = "amqp://guest:guest@localhost:5672/"
    
        throw(payload=payload, uri=uri)
    
        mock_blocking_connection.assert_called_once()
        mock_channel.queue_declare.assert_called_once_with(queue="throw_catch", durable=False)
        mock_channel.basic_publish.assert_called_once()
        mock_connection.close.assert_called_once()


    def test_throw_empty_payload_raises_error(self):
        payload = {}
        uri = "amqp://guest:guest@localhost:5672/"
    
        with pytest.raises(AssertionError, match="Payload dictionary required"):
            throw(payload=payload, uri=uri)


class TestCatch:

    def test_catch_retrieves_single_message(self, mocker):
        mock_connection = mocker.Mock()
        mock_channel = mocker.Mock()
        mock_method = mocker.Mock()
        mock_method.delivery_tag = 1


        test_message = {"tag": "test_tag", "data": "test_data"}
        encoded_message = orjson.dumps(test_message)

        mock_channel.basic_get.return_value = (mock_method, None, encoded_message)
        mock_connection.channel.return_value = mock_channel
        mocker.patch('pika.BlockingConnection', return_value=mock_connection)


        result = catch(uri="amqp://test", queue="test_queue")
        assert len(result) == 1
        assert result[0] == test_message
        
        mock_channel.queue_declare.assert_called_once_with(queue="test_queue", durable=False)
        mock_channel.basic_get.assert_called_once_with("test_queue")
        mock_channel.basic_ack.assert_called_once_with(1)
        mock_connection.close.assert_called_once()


    def test_catch_handles_empty_queue(self, mocker):
        mock_connection = mocker.Mock()
        mock_channel = mocker.Mock()
    
        mock_channel.basic_get.return_value = (None, None, None)
        mock_connection.channel.return_value = mock_channel
        mocker.patch('pika.BlockingConnection', return_value=mock_connection)

        result = catch(uri="amqp://test", queue="test_queue", count=5)

        assert len(result) == 0
        mock_channel.queue_declare.assert_called_once_with(queue="test_queue", durable=False)
        mock_channel.basic_get.assert_called_once_with("test_queue")
        mock_channel.basic_ack.assert_not_called()
        mock_connection.close.assert_called_once()


class TestClear:

    def test_clear_queue_with_valid_uri(self, mocker):
        mock_connection = mocker.patch('pika.BlockingConnection')
        mock_channel = mock_connection.return_value.channel.return_value
        test_uri = "amqp://guest:guest@localhost:5672/"
        clear(uri=test_uri)
        mock_connection.assert_called_once_with(pika.URLParameters(test_uri))
        mock_channel.queue_delete.assert_called_once_with(queue="throw_catch")
        mock_connection.return_value.close.assert_called_once()

    def test_clear_queue_with_empty_uri(self):
        empty_uri = ""
        with pytest.raises(AssertionError, match="AMQP uri required and must be string"):
            clear(uri=empty_uri)
