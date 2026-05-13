"""Public RabbitMQ helpers for throwing and catching messages."""

import datetime as dt
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple

import orjson
import pika


LOGGER = logging.getLogger(__name__)
DEFAULT_QUEUE = "throw_catch"
MAX_NAME_LENGTH = 255
MAX_URI_LENGTH = 255


def _validate_uri(uri: Optional[str]) -> str:
    assert (
        isinstance(uri, str) and 0 < len(uri) <= MAX_URI_LENGTH
    ), "AMQP uri required and must be string"
    return uri


def _validate_ascii_name(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None

    assert (
        isinstance(value, str) and value.isascii() and 0 < len(value) <= MAX_NAME_LENGTH
    ), f"Invalid {field_name} name"
    return value


def _open_channel(uri: str, queue_name: str) -> Tuple[pika.BlockingConnection, Any]:
    connection = pika.BlockingConnection(pika.URLParameters(uri))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=False)
    return connection, channel


def throw(
    payload: Optional[Dict[str, Any]] = None,
    tag: Optional[str] = None,
    uri: Optional[str] = None,
    routing_key: str = DEFAULT_QUEUE,
    ttl: int = 180,
) -> None:
    """Send a message to RabbitMQ."""

    assert isinstance(payload, dict) and payload, "Payload dictionary required"
    validated_uri = _validate_uri(uri)
    validated_routing_key = _validate_ascii_name(routing_key, "routing key")
    validated_tag = _validate_ascii_name(tag, "tag")
    assert isinstance(ttl, int) and ttl >= 0, "TTL message must be positive integer"

    stack = traceback.extract_stack()
    filename, lineno, function_name, _ = stack[-2]

    connection = None
    try:
        connection, channel = _open_channel(validated_uri, validated_routing_key)
        message = {
            "payload": payload,
            "tag": validated_tag,
            "routing_key": validated_routing_key,
            "ttl": ttl,
            "filename": filename,
            "function_name": function_name,
            "lineno": lineno,
            "send_datetime": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        publish_kwargs = {
            "exchange": "",
            "routing_key": validated_routing_key,
            "body": orjson.dumps(message, default=str),
        }

        if ttl > 0:
            publish_kwargs["properties"] = pika.BasicProperties(
                expiration=str(60000 * ttl)
            )

        channel.basic_publish(**publish_kwargs)
    except Exception:
        LOGGER.exception("Failed to publish message to RabbitMQ")
    finally:
        if connection:
            connection.close()


def catch(
    tag: Optional[str] = None,
    uri: Optional[str] = None,
    queue: str = DEFAULT_QUEUE,
    count: int = 1,
) -> List[Dict[str, Any]]:
    """Receive up to ``count`` messages from a RabbitMQ queue."""

    validated_uri = _validate_uri(uri)
    validated_queue = _validate_ascii_name(queue, "queue")
    validated_tag = _validate_ascii_name(tag, "tag")
    assert isinstance(count, int) and count > 0, "Count must be positive integer"

    messages: List[Dict[str, Any]] = []
    connection, channel = _open_channel(validated_uri, validated_queue)

    try:
        for _ in range(count):
            method_frame, _header_frame, body = channel.basic_get(validated_queue)
            if not method_frame:
                break

            message = orjson.loads(body)
            if not validated_tag or message.get("tag") == validated_tag:
                messages.append(message)
                channel.basic_ack(method_frame.delivery_tag)
    finally:
        connection.close()

    return messages


def clear(
    uri: Optional[str] = None,
    queue: str = DEFAULT_QUEUE,
) -> None:
    """Delete a RabbitMQ queue."""

    validated_uri = _validate_uri(uri)
    validated_queue = _validate_ascii_name(queue, "queue")

    connection, channel = _open_channel(validated_uri, validated_queue)
    try:
        channel.queue_delete(queue=validated_queue)
    finally:
        connection.close()
