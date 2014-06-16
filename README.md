## Contact support@pubnub.com for all questions

#### [PubNub](http://www.pubnub.com) Real-time Data Network
##### Clients for Python, including Twisted and Tornado


## Installation
```
pip install pubnub==3.5.0
```

If you prefer to use the previous version of PubNub, run this pip commandline to revert
```
pip install pubnub==3.3.5
```


Examples and instructions for migrating from older versions of sdk are available in 
README.md, migration.md and examples directories under specific platforms.

[Base Python - Everyday python for your scripts and apps](python)

[Tornado - For use with the Python Tornado Framework](tornado)

[Twisted - For use with the Python Twisted Framework](twisted)

## Pubnub Console
Pubnub console is a command line app which allows you to do various 
pubnub operations like publish, subscribe, getting history, here now,
presence etc from command line

```
pip install pubnub-console
```

## Contact support@pubnub.com for all questions
=======
## PubNub 3.3 Web Data Push Cloud-hosted API - PYTHON
#### www.pubnub.com - PubNub Web Data Push Service in the Cloud. 
#### http://github.com/pubnub/python

## Major Upgrade to 3.6 underway! In the meantime, we've provided Python 3 beta support in the python3 branch.

Contact us at support@pubnub.com if you have any questions in the meantime.

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
