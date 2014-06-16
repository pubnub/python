## PubNub 3.5.0 Web Data Push Cloud-hosted API - PYTHON
#### www.pubnub.com - PubNub Web Data Push Service in the Cloud. 
#### http://github.com/pubnub/python


#### Init



```

# Pre 3.5:
#

# New in 3.5+
pubnub = Pubnub(publish_key="demo", subscribe_key="demo", ssl_on=False)

```

#### PUBLISH

```
channel = 'hello_world'
message = 'Hello World !!!'

# Pre 3.5:
#

# New in 3.5+

# Synchronous usage
print pubnub.publish(channel='hello_world', message='Hello World !!!')

# Asynchronous usage

def callback(message):
    print(message)

pubnub.publish(channel, message, callback=callback, error=callback)

```


#### SUBSCRIBE
Pre 3.5.x, subscribe was blocking and would only be terminated via a false return from the callback. In our latest version of the SDK, subscribe is asyncronous, and because of this, usage is a bit different, but the experience is more like our other async SDKs.

```

# Listen for Messages

channel = 'hello_world'

# Pre 3.5:
#

# New in 3.5+

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

#### Unsubscribe
Once subscribed, you can easily, gracefully, unsubscribe:

```
# Pre 3.5:
#

# New in 3.5+

Unsub example
```

#### PRESENCE

```

# Pre 3.5:
#

# New in 3.5+

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

# Pre 3.5:
#

# New in 3.5+

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

# Pre 3.5:
#

# New in 3.5+

# Synchronous usage

print pubnub.history(channel, count=2)

# Asynchronous usage


def callback(message):
    print(message)

pubnub.history(channel, count=2, callback=callback, error=callback)
```
