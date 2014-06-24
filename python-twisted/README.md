## Contact support@pubnub.com for all questions

#### [PubNub](http://www.pubnub.com) Real-time Data Network
##### Twisted Client

## IO Event Loop
Be sure to eventually start the event loop or PubNub won't run!

```
pubnub.start()
```

#### Import
```
from Pubnub import PubnubTwisted as Pubnub
```

#### Init
```
pubnub = Pubnub(publish_key="demo", subscribe_key="demo", ssl_on=False)
```

#### Publish Example
```
channel = 'hello_world'
message = 'Hello World !!!'

# Asynchronous usage


def callback(message):
    print(message)

pubnub.publish(channel, message, callback=callback, error=callback)
```

#### Subscribe Example
```
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

#### History Example
```
def callback(message):
    print(message)

pubnub.history(channel, count=2, callback=callback, error=callback)
```

#### Here Now Example
```
def callback(message):
    print(message)

pubnub.here_now(channel, callback=callback, error=callback)
```

#### Presence Example
```
channel = 'hello_world'

def callback(message, channel):
    print(message)


def error(message):
    print("ERROR : " + str(message))

pubnub.presence(channel, callback=callback, error=callback)
```

#### Unsubscribe Example
```
pubnub.unsubscribe(channel='hello_world')
```

#### Grant Example
```
authkey = "abcd"

def callback(message):
    print(message)

pubnub.grant(channel, authkey, True, True, callback=callback, error=callback)

```

#### Audit Example
```
authkey = "abcd"

def callback(message):
    print(message)

pubnub.audit(channel, authkey, callback=callback, error=callback)
```

#### Revoke Example
```
authkey = "abcd"

def callback(message):
    print(message)

pubnub.revoke(channel, authkey, callback=callback, error=callback)
```


#### IO Event Loop start
```
pubnub.start()
```

## Contact support@pubnub.com for all questions
