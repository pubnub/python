# www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

# PubNub Real-time Push APIs and Notifications Framework
# Copyright (c) 2010 Stephen Blum
# http://www.pubnub.com/


import sys

from pubnub import Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'demo'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or 'abcd'
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

# -----------------------------------------------------------------------
# Initiate Pubnub State
# -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on, daemon=False)

channel = 'ab'


# Asynchronous usage
def callback(message, channel):
    print(str(message) + ' , ' + channel)


def error(message):
    print("ERROR : " + str(message))


def connect(message):
    print("CONNECTED " + str(message))


def reconnect(message):
    print("RECONNECTED " + str(message))


def disconnect(message):
    print("DISCONNECTED " + str(message))


print(pubnub.channel_group_add_channel(channel_group='abc', channel="a"))

pubnub.subscribe_group(channel_groups='abc', callback=callback, error=callback,
                       connect=connect, reconnect=reconnect, disconnect=disconnect)

pubnub.start()
