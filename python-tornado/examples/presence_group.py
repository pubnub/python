# www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

# PubNub Real-time Push APIs and Notifications Framework
# Copyright (c) 2010 Stephen Blum
# http://www.pubnub.com/


import sys

from pubnub import PubnubTornado as Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'demo'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or 'abcd'
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

# -----------------------------------------------------------------------
# Initiate Pubnub State
# -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on)

channel = 'ab'


# Asynchronous usage

def callback_abc(message, channel, real_channel):
    print(str(message) + ' , ' + channel + ', ' + real_channel)
    # pubnub.unsubscribe_group(channel_group='abc')
    # pubnub.stop()


def callback_d(message, channel):
    print(str(message) + ' , ' + channel)


def error(message):
    print("ERROR : " + str(message))


def connect_abc(message):
    print("CONNECTED " + str(message))


def connect_d(message):
    print("CONNECTED " + str(message))
    pubnub.unsubscribe(channel='d')


def reconnect(message):
    print("RECONNECTED " + str(message))


def disconnect(message):
    print("DISCONNECTED " + str(message))


print(pubnub.channel_group_add_channel(channel_group='abc', channel="bn"))

pubnub.presence_group(channel_group='abc', callback=callback_abc, error=error)

pubnub.presence(channel='d', callback=callback_d, error=error)

pubnub.start()
