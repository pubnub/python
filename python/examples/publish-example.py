## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

import sys
from Pubnub import PubnubAsync as Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'demo'
cipher_key = len(
    sys.argv) > 4 and sys.argv[4] or ''  # (Cipher key is Optional)
auth_key = len(
    sys.argv) > 5 and sys.argv[4] or 'abcd'  # (Cipher key is Optional)
ssl_on = len(sys.argv) > 6 and bool(sys.argv[5]) or False

## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
pubnub = Pubnub(
    publish_key, subscribe_key, secret_key, cipher_key, auth_key, ssl_on, pooling=True)
crazy = 'hello_world'

## -----------------------------------------------------------------------
## Publish Example
## -----------------------------------------------------------------------


def publish_complete(info):
    print(info)


def publish_error(info):
    print('ERROR : ' + str(info))

import time
start = time.time()
for i in range(1,100):
    print pubnub.publish(crazy, 'hello world-' + str(i))
end = time.time()
print(end - start);
