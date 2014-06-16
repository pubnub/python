## PubNub 3.5.0 Web Data Push Cloud-hosted API - PYTHON TWISTED
#### www.pubnub.com - PubNub Web Data Push Service in the Cloud. 
#### http://github.com/pubnub/python

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

#### IO Event Loop
##### VERY IMPORTANT TO ADD THIS LINE AT THE VERY BOTTOM!

```
pubnub.start()
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

#### IO Event Loop start
```
pubnub.start()
```