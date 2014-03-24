import sys
sys.path.append('.')
sys.path.append('..')
from Pubnub import Pubnub

## Initiate Class
pubnub = Pubnub( publish_key='demo', subscribe_key='demo', ssl_on=False )

## Publish Example
info = pubnub.publish({
    'channel' : 'hello_world',
    'message' : {
        'some_text' : 'Hello my World'
    }
})
print(info)

