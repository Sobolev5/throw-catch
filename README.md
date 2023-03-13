# RabbitMQ throw & catch messages

## Install
To install run:
```no-highlight
pip install throw-catch
```

Add the following line at the top of your *.py file:
```python
from throw_catch import throw, catch 
```
  
Now you can send messages to RabbitMQ queue `amq.direct`.`throw_catch` (by default):
```python
import os
AMQP_URI = os.getenv("AMQP_URI")

payload = {"hello": "world"}  
throw(payload=payload, uri=AMQP_URI) 
throw(payload=payload, uri=AMQP_URI, routing_key="some_routing_key") # custom routing key (direct)
for _ in range(10):
    throw(payload=payload, tag="some_tag", uri=AMQP_URI, routing_key="some_routing_key") # custom tag && custom routing key
``` 
   
Catch messages from RabbitMQ:
```python
import os
AMQP_URI = os.getenv("AMQP_URI")

catch(uri=AMQP_URI) # {"hello": "world"} 
catch(uri=AMQP_URI, queue="some_routing_key") # catch 10 messages from `some_routing_key` queue (direct) 
catch(tag="some_tag", uri=AMQP_URI, queue="some_routing_key", count=10) # catch 10 messages from `some_routing_key` queue (direct) with tag `some_tag`
```
  
### Test 
```sh
tox
```