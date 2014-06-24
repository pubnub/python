## Contact support@pubnub.com for all questions

#### [PubNub](http://www.pubnub.com) Real-time Data Network
##### Standalone Python Client

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

#### SUBSCRIBE Synchronous ( compatible with pre-3.5 )
Runs in tight loop if callback return True.
Loop ends when callback return False
```
# Listen for Messages

channel = 'hello_world'

def callback(message):
    print(message)
    return True

pubnub.subscribe_sync(channel, callback=callback)
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

#### GRANT

```
authkey = "abcd"

# Synchronous usage
print pubnub.grant(channel, authkey, True, True)

# Asynchronous usage


def callback(message):
    print(message)

pubnub.grant(channel, authkey, True, True, callback=callback, error=callback)
```

#### AUDIT

```
authkey = "abcd"

# Synchronous usage
print pubnub.audit(channel, authkey)

# Asynchronous usage


def callback(message):
    print(message)

pubnub.audit(channel, authkey, callback=callback, error=callback)
```

#### REVOKE

```
authkey = "abcd"

# Synchronous usage
print pubnub.revoke(channel, authkey)

# Asynchronous usage


def callback(message):
    print(message)

pubnub.revoke(channel, authkey, callback=callback, error=callback)
```

## Contact support@pubnub.com for all questions
