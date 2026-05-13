# RabbitMQ throw & catch messages

## Install
To install run:
```no-highlight
uv add throw-catch
```

Add the following line at the top of your *.py file:
```python
from throw_catch import catch, clear, throw
```

By default, the library publishes to and reads from the `throw_catch` queue:
```python
import os

AMQP_URI = os.getenv("AMQP_URI")

payload = {"hello": "world"}

throw(payload=payload, uri=AMQP_URI)
throw(payload=payload, uri=AMQP_URI, routing_key="some_routing_key")

for _ in range(10):
    throw(
        payload=payload,
        tag="some_tag",
        uri=AMQP_URI,
        routing_key="some_routing_key",
    )
```

Catch messages from RabbitMQ:
```python
import os

AMQP_URI = os.getenv("AMQP_URI")

catch(uri=AMQP_URI)
catch(uri=AMQP_URI, queue="some_routing_key")
catch(tag="some_tag", uri=AMQP_URI, queue="some_routing_key", count=10)

clear(uri=AMQP_URI, queue="some_routing_key")
```

## Notes
- Supported Python versions start at 3.11.
- `ttl` is specified in minutes. Set `ttl=0` to publish without expiration.

## Development
```sh
uv sync --dev
```

## Test
```sh
uv run pytest
```
