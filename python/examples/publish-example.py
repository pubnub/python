import sys
sys.path.append('.')
sys.path.append('..')
from Pubnub import Pubnub

## Initiate Class
pubnub = Pubnub( publish_key='demo', subscribe_key='demo', cipher_key='enigma', ssl_on=False )
#pubnub = Pubnub( publish_key='demo', subscribe_key='demo', ssl_on=False )

## Publish Example
info = pubnub.publish({
    'channel' : 'abcd',
    'message' : {
        'iam' : 'object'
    }
})
print(info)

info = pubnub.publish({
    'channel' : 'abcd',
    'message' : "hi I am string"
})
print(info)

info = pubnub.publish({
    'channel' : 'abcd',
    'message' : 1234
})
print(info)

info = pubnub.publish({
    'channel' : 'abcd',
    'message' : "1234"
})
print(info)

info = pubnub.publish({
    'channel' : 'abcd',
    'message' : [
        'i' , 'am', 'array'
    ]
})
print(info)
