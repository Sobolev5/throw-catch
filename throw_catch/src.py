import pika
import logging
import orjson
import traceback
import datetime
from typing import Union


def throw(
    payload: dict = {},
    tag: str = None,
    uri: str = None,
    routing_key: str = "throw_catch",
    ttl: int = 180,
) -> Union[None, str]:
    """Throw message in RabbitMQ.

    Args:
        payload (dict, optional): payload dict. Defaults to {}.
        tag (str, optional): message tag. Defaults to None.
        uri (str, optional): AMQP uri. Defaults to None.
        routing_key (str, optional): routring key. Defaults to "throw_catch".
        ttl (int, optional): time to live. Defaults to 180.
    """
    assert bool(payload), "Payload dictionary required"
    assert (
        isinstance(uri, str) and len(uri) > 0 and len(uri) < 256
    ), "AMQP uri required and must be string"
    assert (
        isinstance(routing_key, str)
        and routing_key.isascii()
        and len(routing_key) < 256
    ), "Invalid routing key name"

    if tag:
        assert (
            isinstance(tag, str) and tag.isascii() and len(tag) < 256
        ), "Invalid tag name"

    assert isinstance(ttl, int) and ttl >= 0, "TTL message must be positive integer"

    stack = traceback.extract_stack()
    filename, lineno, function_name, code = stack[-2]

    connection = None
    channel = None

    try:
        connection = pika.BlockingConnection(pika.URLParameters(uri))
        channel = connection.channel()
        channel.queue_declare(queue=routing_key, durable=False)
    except Exception as e:
        logging.exception(f"{e}")

    if connection and channel:
        try:
            body = {
                "payload": payload,
                "tag": tag,
                "routing_key": routing_key,
                "ttl": ttl,
                "filename": filename,
                "function_name": function_name,
                "lineno": lineno,
                "send_datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            body = orjson.dumps(body, default=str)
            if ttl == 0:
                channel.basic_publish(
                    exchange="",
                    routing_key=routing_key,
                    body=body,
                )
            else:
                channel.basic_publish(
                    exchange="",
                    routing_key=routing_key,
                    properties=pika.BasicProperties(expiration=str(60000 * ttl)),
                    body=body,
                )
        except Exception:
            logging.exception("{e}")

    else:
        logging.exception(
            f"pika channel opening failed connection={connection} channel={channel}"
        )

    if connection:
        connection.close()


def catch(
    tag: str = None,
    uri: str = None,
    queue: str = "throw_catch",
    count: int = 1,
) -> list[dict]:
    """Catch message from RabbitMQ.

    Args:
        tag (str, optional): message tag. Defaults to None.
        uri (str, optional): AMQP uri. Defaults to None.
        queue (str, optional): queue. Defaults to "throw_catch".
        count (int, optional): count messages. Defaults to 1.

    Returns:
        list[dict]: _description_
    """

    assert (
        isinstance(uri, str) and len(uri) > 0 and len(uri) < 256
    ), "AMQP uri required and must be string"
    assert (
        isinstance(queue, str) and queue.isascii() and len(queue) < 256
    ), "Invalid queue name"

    if tag:
        assert (
            isinstance(tag, str) and tag.isascii() and len(tag) < 256
        ), "Invalid tag name"

    messages = []
    connection = pika.BlockingConnection(pika.URLParameters(uri))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=False)

    for _ in range(count):
        method_frame, header_frame, body = channel.basic_get(queue)
        if method_frame:
            message = orjson.loads(body.decode())
            if message:
                if not tag or (message["tag"] == tag):
                    messages.append(message)
                    channel.basic_ack(method_frame.delivery_tag)
        else:
            break

    connection.close()
    return messages


def clear(
    uri: str = None,
    queue: str = "throw_catch",
) -> None:
    """CLear messages queue.

    Args:
        uri (str, optional): AMQP uri.
        queue (str, optional): queue. Defaults to "throw_catch".
    """

    assert (
        isinstance(uri, str) and len(uri) > 0 and len(uri) < 256
    ), "AMQP uri required and must be string"
    assert (
        isinstance(queue, str) and queue.isascii() and len(queue) < 256
    ), "Invalid queue name"

    connection = pika.BlockingConnection(pika.URLParameters(uri))
    channel = connection.channel()
    channel.queue_delete(queue=queue)
    connection.close()
