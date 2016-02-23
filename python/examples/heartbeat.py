# www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

# PubNub Real-time Push APIs and Notifications Framework
# Copyright (c) 2010 Stephen Blum
# http://www.pubnub.com/

import gevent.monkey
import random
import sys
from datetime import datetime
from pubnub import Pubnub as Pubnub

gevent.monkey.patch_all()

# from pubnub import PubnubTornado as Pubnub
# from pubnub import PubnubTwisted as Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'ds'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'ds'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'ds'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or ''
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

# -----------------------------------------------------------------------
# Initiate Pubnub State
# -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on, uuid="test-" + str(random.random()))


def x(url):
    print(url)


# pubnub.set_http_debug(x)

channel = 'ab,cd,ef'
channel_group = "abg,cdg"


def set_heartbeat(*argv):
    print("Change Heartbeat to ", argv[0])
    pubnub.set_heartbeat(argv[0], argv[1], argv[2])


def set_heartbeat_interval(*argv):
    pubnub.set_heartbeat_interval(argv[0])


# pubnub.timeout(0, set_heartbeat, 8)

# Asynchronous usage
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


pubnub.channel_group_add_channel("abg", "abcd")
pubnub.channel_group_add_channel("cdg", "efgh")

pubnub.subscribe(channels=channel, callback=callback, error=callback,
                 connect=connect, reconnect=reconnect, disconnect=disconnect)

pubnub.subscribe_group(channel_groups=channel_group, callback=callback, error=callback,
                       connect=connect, reconnect=reconnect, disconnect=disconnect)


def cb(resp):
    print(datetime.now().strftime('%H:%M:%S'), resp)


def err(resp):
    print(datetime.now().strftime('%H:%M:%S'), resp)


pubnub.timeout(5, set_heartbeat, 120, cb, err)
pubnub.timeout(90, set_heartbeat, 60, cb, err)
pubnub.timeout(180, set_heartbeat, 30, cb, err)
pubnub.timeout(240, set_heartbeat, 15, cb, err)
pubnub.timeout(300, set_heartbeat, 8, cb, err)
# pubnub.timeout(360, pubnub.stop_heartbeat)


'''
import time
while True:
    time.sleep(10)
'''

pubnub.start()
