## PubNub 3.5.0 Web Data Push Cloud-hosted API - PYTHON
#### www.pubnub.com - PubNub Web Data Push Service in the Cloud. 
#### http://github.com/pubnub/python


#### Init

```
pubnub = Pubnub(publish_key="demo", subscribe_key="demo", ssl_on=False)

```

#### PUBLISH

```
channel = 'hello_world'
message = 'Hello World !!!'

# Synchronous usage
print pubnub.publish(channel='hello_world', message='Hello World !!!')

# Asynchronous usage

def callback(message):
    print(message)

pubnub.publish(channel, message, callback=callback, error=callback)

```


#### SUBSCRIBE

```
# Listen for Messages

channel = 'hello_world'

def callback(message, channel):
    print(message)


def error(message):
    print("ERROR : " + str(message))


def connect(message):
    print("CONNECTED")


def reconnect(message):
    print("RECONNECTED")


def disconnect(message):
    print("DISCONNECTED")


pubnub.subscribe(channel, callback=callback, error=callback,
                 connect=connect, reconnect=reconnect, disconnect=disconnect)
```

#### UNSUBSCRIBE

```
# Listen for Messages

channel = 'hello_world'

pubnub.unsubscribe(channel=channel)
```


#### PRESENCE

```
# Listen for Presence Event Messages

channel = 'hello_world'

def callback(message, channel):
    print(message)


def error(message):
    print("ERROR : " + str(message))



pubnub.presence(channel, callback=callback, error=callback)
```

#### HERE_NOW

```
# Get info on who is here right now!

channel = 'hello_world'

# Synchronous usage
print pubnub.here_now(channel)


# Asynchronous usage

def callback(message):
    print(message)

pubnub.here_now(channel, callback=callback, error=callback)
```

#### HISTORY

```
# Synchronous usage

print pubnub.history(channel, count=2)

# Asynchronous usage


def callback(message):
    print(message)

pubnub.history(channel, count=2, callback=callback, error=callback)
```
