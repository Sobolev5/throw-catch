# throw-catch

Small RabbitMQ helpers for publishing, receiving, and clearing JSON messages with minimal setup.

`throw-catch` is designed for lightweight workflows where you want to drop structured messages into a queue, fetch them back in tests or background jobs, and keep the API surface tiny.

## Highlights

- Simple `throw`, `catch`, and `clear` functions.
- JSON serialization via `orjson`.
- Optional message tags for selective reads.
- Per-message TTL support in minutes.
- Works with Python `3.11+`.
- Managed with `uv`.

## Installation

```sh
uv add throw-catch
```

## Quick Start

```python
import os

from throw_catch import catch, clear, throw

amqp_uri = os.getenv("AMQP_URI")

throw(payload={"hello": "world"}, uri=amqp_uri)

messages = catch(uri=amqp_uri)
print(messages)

clear(uri=amqp_uri)
```

## Usage

### Publish messages

```python
from throw_catch import throw

throw(
    payload={"event": "user.created", "user_id": 42},
    uri="amqp://guest:guest@localhost:5672/",
)

throw(
    payload={"event": "invoice.ready"},
    tag="billing",
    routing_key="events.billing",
    ttl=30,
    uri="amqp://guest:guest@localhost:5672/",
)
```

Notes:
- `payload` must be a non-empty dictionary.
- `ttl` is in minutes.
- `ttl=0` publishes without expiration.

### Receive messages

```python
from throw_catch import catch

messages = catch(
    uri="amqp://guest:guest@localhost:5672/",
    queue="events.billing",
    tag="billing",
    count=10,
)
```

`catch` returns a list of decoded message dictionaries and acknowledges only the messages it actually returns.

### Clear a queue

```python
from throw_catch import clear

clear(
    uri="amqp://guest:guest@localhost:5672/",
    queue="events.billing",
)
```

## API

### `throw(payload, tag=None, uri=None, routing_key="throw_catch", ttl=180)`

Publishes a message to the target queue.

### `catch(tag=None, uri=None, queue="throw_catch", count=1)`

Reads up to `count` messages from the queue and returns them as a list.

### `clear(uri=None, queue="throw_catch")`

Deletes the target queue.

## Development

Install dependencies:

```sh
uv sync --dev
```

Run tests:

```sh
uv run pytest
```
