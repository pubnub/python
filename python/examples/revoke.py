## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/


import sys
from Pubnub import Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'pam'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'pam'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'pam'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or ''
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on)
channel = 'hello_world'
authkey = "abcd"

# Synchronous usage
print pubnub.revoke(channel, authkey)

# Asynchronous usage


def callback(message):
    print(message)

pubnub.revoke(channel, authkey, callback=callback, error=callback)
