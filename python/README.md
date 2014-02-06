## PubNub 3.3 Web Data Push Cloud-hosted API - PYTHON
#### www.pubnub.com - PubNub Web Data Push Service in the Cloud. 
#### http://github.com/pubnub/pubnub-api/tree/master/python


#### Init

```
pubnub = Pubnub(
    "demo",  ## PUBLISH_KEY
    "demo",  ## SUBSCRIBE_KEY
    None,    ## SECRET_KEY
    False    ## SSL_ON?
)
```

#### PUBLISH

```
info = pubnub.publish({
    'channel' : 'hello_world',
    'message' : {
        'some_text' : 'Hello my World'
    }
})
print(info)
```


#### SUBSCRIBE

```
# Listen for Messages *BLOCKING*
def receive(message) :
    print(message)
    return True

pubnub.subscribe({
    'channel'  : 'hello_world',
    'callback' : receive 
})
```


#### PRESENCE

```
# Listen for Presence Event Messages *BLOCKING*

def pres_event(message) :
    print(message)
    return True

pubnub.presence({
    'channel'  : 'hello_world',
    'callback' : receive 
})
```

#### HERE_NOW

```
# Get info on who is here right now!

here_now = pubnub.here_now({
    'channel' : 'hello_world',
})

print(here_now['occupancy'])
print(here_now['uuids'])
```

#### Channel Analytics

```
analytics = pubnub.analytics({
    'channel'  : 'channel-name-here', ## Leave blank for all channels
    'limit'    : 100,                 ## aggregation range
    'ago'      : 0,                   ## minutes ago to look backward
    'duration' : 100                  ## minutes offset
})
print(analytics)

```

#### HISTORY

```
# Load Previously Published Messages
history = pubnub.detailedHistory({
    'channel'   : 'my_channel',
    'end'       : my_end_time_token, # Optional
    'start'     : my_start_time_token, # Optional
    'count'     : num_of_msgs_to_return # Optional, default is 100
})
print(history)
```
