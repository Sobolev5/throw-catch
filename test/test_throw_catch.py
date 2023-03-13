import os
from throw_catch import throw, catch, clear


def test_throw_catch():

    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    AMQP_URI = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/vhost"

    payload = {"hello": "world"}  

    throw(payload=payload, routing_key="some_routing_key", uri=AMQP_URI) 
    messages = catch(uri=AMQP_URI, queue="some_routing_key")
    assert len(messages) > 0, "No messages in query"

    clear(uri=AMQP_URI, queue="some_routing_key") 
    messages = catch(uri=AMQP_URI, queue="some_routing_key")
    assert len(messages) == 0, "Queue clear failed"
