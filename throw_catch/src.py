import pika
import logging
import orjson
import traceback
import datetime
from typing import Union


def throw(payload:dict={}, tag: str="throwed", uri:str=None, routing_key: str="throw_catch", ttl :int=180, **kwargs) -> Union[None, str]:
    """ 
    throw [send message to rabbitmq]:
    payload: dict ~ payload data 
    tag: str ~ message tag  
    uri: str ~ rabbitmq uri 
    routing_key: str ~ routing key name   
    ttl: int ~ message time to live (in minutes)
    """

    assert bool(payload), "Payload dictionary required" 
    assert isinstance(uri, str) and len(uri) > 0 and len(uri) < 256, "AMQP uri required and must be string" 
    assert isinstance(routing_key, str) and routing_key.isascii() and len(routing_key) < 256, "Invalid routing key name"  
    assert isinstance(tag, str) and tag.isascii() and len(tag) > 0 and len(tag) < 256, "Invalid tag name or tag is empty" 
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
                "send_datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            }

            body = orjson.dumps(body, default=str)      
            if ttl == 0:
                channel.basic_publish(exchange="", routing_key=routing_key, body=body)                
            else:
                channel.basic_publish(exchange="", routing_key=routing_key, properties=pika.BasicProperties(expiration=str(60000*ttl)), body=body)                           
        except Exception as e:
            logging.exception("{e}")    

    else:
        logging.exception(f"pika channel opening failed connection={connection} channel={channel}")  

    if connection:
        connection.close()


def catch(tag: str="throwed", uri: str=None, queue: str="throw_catch", count: int=1, **kwargs) -> list[dict]:
    """ 
    catch [get message from rabbitmq]:
    tag:str ~ message tag
    uri: str ~ rabbitmq uri 
    queue:str ~ message queue
    count:int ~ messages num
    """

    assert isinstance(uri, str) and len(uri) > 0 and len(uri) < 256, "AMQP uri required and must be string" 
    assert isinstance(queue, str) and queue.isascii() and len(queue) < 256, "Invalid queue name"
    assert isinstance(tag, str) and tag.isascii() and len(tag) > 0 and len(tag) < 256, "Invalid tag name or tag is empty" 

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


def clear(uri: str=None, queue: str="throw_catch", **kwargs) -> None:
    """ 
    clear [clear all messages in rabbitmq queue]:
    tag:str ~ message tag
    uri: str ~ rabbitmq uri 
    queue:str ~ message queue
    count:int ~ messages num
    """

    assert isinstance(uri, str) and len(uri) > 0 and len(uri) < 256, "AMQP uri required and must be string" 
    assert isinstance(queue, str) and queue.isascii() and len(queue) < 256, "Invalid queue name"

    connection = pika.BlockingConnection(pika.URLParameters(uri))
    channel = connection.channel()
    channel.queue_delete(queue=queue)
    connection.close()


