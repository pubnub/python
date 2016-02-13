# www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

# PubNub Real-time Push APIs and Notifications Framework
# Copyright (c) 2010 Stephen Blum
# http://www.pubnub.com/


import sys
import time
from gevent import monkey
from pubnub import Pubnub

monkey.patch_all()


publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'demo'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or ''
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

# -----------------------------------------------------------------------
# Initiate Pubnub State
# -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on)


def log(a):
    print(a)


pubnub.set_http_debug(log)

# Synchronous usage
print(pubnub.state(channel='abcd', uuid='33c72389-1110-4312-9444-4dd24ade1d57', state={'a': 'b'}))


# Asynchronous usage


def callback(message):
    print(message)


pubnub.state(channel='abcd', uuid='33c72389-1110-4312-9444-4dd24ade1d57', state={'a': 'b'}, callback=callback,
             error=callback)

time.sleep(5)

# Synchronous usage
print(pubnub.state(channel='abcd', uuid='33c72389-1110-4312-9444-4dd24ade1d57'))


# Asynchronous usage


def callback(message):
    print(message)


pubnub.state(channel='abcd', uuid='33c72389-1110-4312-9444-4dd24ade1d57', callback=callback, error=callback)

time.sleep(5)

# Synchronous usage
print(pubnub.state(channel='abcd'))


# Asynchronous usage


def callback(message):
    print(message)


pubnub.state(channel='abcd', callback=callback, error=callback)

time.sleep(5)

# Synchronous usage
print(pubnub.state(channel='abcd', state={'a': 'b'}))


# Asynchronous usage


def callback(message):
    print(message)


pubnub.state(channel='abcd', state={'a': 'b'}, callback=callback, error=callback)

time.sleep(5)

# Synchronous usage
print(pubnub.state(channel='abcd'))


# Asynchronous usage


def callback(message):
    print(message)


pubnub.state(channel='abcd', callback=callback, error=callback)

time.sleep(5)

# Synchronous usage
print(pubnub.state(channel='abcd'))


# Asynchronous usage


def callback(message):
    print(message)


pubnub.state(channel='abcd', callback=callback, error=callback)
